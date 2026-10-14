import cProfile
import pstats
import sys

from devlens.project import main

sys.argv = ["devlens", "scan", "."]

profiler = cProfile.Profile()
profiler.enable()

main()
profiler.disable()

stat = pstats.Stats(profiler)

stat.sort_stats("cumulative")
stat.print_stats(15)
