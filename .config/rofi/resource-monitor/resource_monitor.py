#!/bin/env python3

import subprocess
import os
import argparse
from dataclasses import dataclass

# use SI unit (1000) or IEC unit (1024)
KILO = 1000  # SI
# KILO = 1024  # IEC
CURRENT_SCRIPT_PID = os.getpid()


def formatBytes(kBytes: int) -> str:
    orderNames = {0: "k", 3: "M", 6: "G", 9: "T"}

    kBytesNew = float(kBytes)
    order = 0
    while kBytesNew >= KILO:
        kBytesNew /= KILO
        order += 3

    if order < 6:
        kBytesNew = int(kBytesNew)
    else:
        kBytesNew = round(kBytesNew, 1)

    return str(kBytesNew) + orderNames[order]


def getTotalMemory() -> int:
    try:
        with open("/proc/meminfo", "r") as meminfo:
            totalMemory = int(meminfo.readline().split()[1])
    except:
        try:
            inputStr: str = input(
                "error reading /proc/meminfo file. please input your system total memory in GB: "
            )
            totalMemory = int(KILO * KILO * float(inputStr))
            raise  # temp
        except:
            totalMemory = 0

    return totalMemory


def calculateCpuUsage(utime, stime, starttime) -> float:
    uptime: float = float(open("/proc/uptime").read().split()[0])  # in seconds
    clk_tck = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
    utime = utime / clk_tck  # in seconds
    stime = stime / clk_tck  # in seconds
    starttime = starttime / clk_tck  # in seconds

    pcpu = 100 * (utime + stime) / (uptime - starttime)  # in percent

    return pcpu


# read /proc/{$pid}/status file directly
# TODO: read from /proc/[pid]/statm instead
# FIXME: not working on Fedora 37, different field get queried
def getSwapFromPid(pid: list) -> int:
    totalSwap = 0

    for p in pid:
        file = f"/proc/{p}/status"

        try:
            with open(file, "r") as procStatus:
                line: str = procStatus.readlines()[30].strip()
                swap = int(line.split()[1]) if line.startswith("VmSwap") else 0
                totalSwap += swap

        except FileNotFoundError:
            pass

    return totalSwap


@dataclass
class Process:
    pid: list[int]
    comm: str
    pcpu: float
    mem: int
    swap: int


class ProcessArray:
    def __init__(self) -> None:
        self.__processArray: list[Process] = list()
        self.__iter_index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.__iter_index >= len(self.__processArray):
            raise StopIteration
        else:
            process: Process = self.__processArray[self.__iter_index]
            self.__iter_index += 1
            return process

    def __sortProcessArray(self, sortBy: str, reverse: bool = False) -> None:
        processArray = self.__processArray

        def getAttribute(process: Process, attr: str):
            if attr == "cpu":
                return process.pcpu
            elif attr == "mem":
                return process.mem
            elif attr == "swap":
                return process.swap
            elif attr == "comm":
                return process.comm
            elif attr == "pid":
                return process.pid
            else:
                return process.comm  # fallback

        self.__processArray = sorted(
            processArray,
            key=lambda process: getAttribute(process, sortBy),
            reverse=not reverse,
        )

    # get a unique array of sorted processes by comm names
    @classmethod
    def getProcesses(cls, skipCurrentPid: bool):
        processArray = ProcessArray()
        processes = processArray.__processArray

        # used to keep track of unique processNames, thus used in order to filter unique processes only
        processNames = dict()

        # use a command (linux command) to get processes list (outputs a string)
        # field index:       0   1    2   3
        command = f"ps -ewo pid,pcpu,rss,comm | tail -n+2 | tr -s ' '"  # the command outputs a sorted process by name (comm)
        result = (
            subprocess.run(command, shell=True, stdout=subprocess.PIPE)
            .stdout.decode("utf-8")
            .rstrip()
        )

        lines = result.split("\n")

        index = -1  # used to keep track of last process added to the processes array
        for line in lines:
            line = line.split(maxsplit=3)

            if len(line) == 0:
                continue  # if there's nothing in the line, skip it

            (pid, pcpu, rss, comm) = line
            pid = int(pid)
            pcpu = float(pcpu)
            rss = int(rss)
            comm = comm.split("/")[0]  # some process have sub-processes that
            # named something like: "parentProcess/subProcess", I take only the parentProcess name

            # skip current script process for being shown
            if skipCurrentPid and pid == CURRENT_SCRIPT_PID:
                continue

            if comm in processNames:
                sameProcessIndex = processNames[comm]
                process: Process = processes[sameProcessIndex]
                process.pid.append(pid)
                process.pcpu += pcpu
                process.mem += rss
            else:
                process = Process([pid], comm, pcpu, rss, 0)
                processes.append(process)  # add new process to the processes array
                index += 1
                processNames[
                    comm
                ] = index  # add new process name to the processName dict to inform that it is the first occured process
        return processArray

    def findProcessByComm(self, comm: str, indexOnly: bool = False):
        found = False
        count = -1
        processes = self.__processArray

        process: Process | None = None
        for process in processes:
            count += 1
            if process.comm == comm:
                found = True
                break

        if not found:
            process = None
            count = -1

        return count if indexOnly else (process, count)

    def print(
        self,
        sortBy: str = "cpu",
        amount: int = -1,
        reverse: bool = False,
        withHeader=False,
    ) -> None:
        self.__sortProcessArray(sortBy, reverse)  # sort processArray

        processArraySize = len(self.__processArray)
        if amount < 0 or amount > processArraySize:
            amount = processArraySize

        firstColumnLen = (
            max(len(str(amount)), len("no. ")) if withHeader else len(str(amount))
        )

        maxCommLen = 25
        shownPidNum = 4
        fmt = f"{{:>{firstColumnLen}.{firstColumnLen}}} | {{:>5.5}} | {{:>4.4}} | {{:>4.4}} | {{:>4.4}} | {{:<{maxCommLen}.{maxCommLen}}} | {{}}"

        if withHeader:
            print(fmt.format("no.", "pcpu", "pmem", "mem", "swap", "comm", "pids"))
            sep = "-" * maxCommLen  # comm is highest width
            print(fmt.format(sep, sep, sep, sep, sep, sep, sep))
        for count, process in enumerate(self.__processArray[:amount]):
            p = process
            countStr = str(count + 1)
            memStr = formatBytes(p.mem)
            swapStr = formatBytes(p.swap)

            shownPids = p.pid[: min(len(p.pid), shownPidNum)]
            shownPids = f"({len(p.pid)}) [{', '.join(map(str, shownPids)) + ', ...' * (len(p.pid)> shownPidNum)}]"
            pmem = 100 * p.mem / getTotalMemory()
            (pcpu, pmem, comm) = (str(round(p.pcpu, 1)), str(round(pmem, 1)), p.comm)
            print(fmt.format(countStr, pcpu, pmem, memStr, swapStr, comm, shownPids))


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "mode",
        help="choose which process information to be sorted with",
        choices=["cpu", "mem", "swap", "comm", "pid", "total"],
        default=None,
    )
    parser.add_argument(
        "-d",
        "--no-header",
        help="print without header",
        action="store_true",
    )
    parser.add_argument(
        "-r",
        "--reverse",
        help="reverse displayed list",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--skip-current",
        help="skip and ignore the process of this script from being displayed",
        action="store_true",
    )
    parser.add_argument(
        "-n",
        "--num",
        help="number of processes to display",
        action="store",
        metavar="N",
        type=int,
        default=-1,
    )

    args = parser.parse_args()

    CHOICE = args.mode
    COUNT = args.num
    REVERSE = args.reverse
    SHOW_TOTAL = args.mode == "total"
    HEADER = not args.no_header
    SKIP = args.skip_current

    processes = ProcessArray.getProcesses(SKIP)

    if SHOW_TOTAL:
        pcpu = 0.0
        mem = 0
        for p in processes:
            pcpu += p.pcpu
            mem += p.mem

        totalMem = getTotalMemory()
        pmem = mem / getTotalMemory() * 100
        print(
            f"CPU: {round(pcpu,1)}% | MEM: {round(pmem,1)}% ({formatBytes(mem)}/{formatBytes(totalMem)})"
        )

    else:
        processes.print(CHOICE, COUNT, REVERSE, HEADER)


if __name__ == "__main__":
    main()
