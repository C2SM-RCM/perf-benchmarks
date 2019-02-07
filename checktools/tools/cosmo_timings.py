def read_file(folder, filename):
    from os import path
    file = open(path.join(folder, filename))
    return file.readlines()

class COSMO_Run:
    def __init__(self, folder, name, cosmolog="exe.log", slurmlog="cosmo_benchmark.out"):
        self.name = name
        self.timings = []
        if slurmlog:
            file = read_file(folder, slurmlog)
            self.timings.append(("total", float(COSMO_Run.get_slurm_timing(file))))
        if cosmolog:
            file = read_file(folder, cosmolog)
            benchmark = COSMO_Run.find_cosmo_benchmark(file)
            self.benchmark_metadata = benchmark
            for result in benchmark:
                tag = result["tag"]
                for val in ["min", "max", "mean"]:
                    idx = "{tag} {val}".format(tag=tag, val=val)
                    self.timings.append((idx, float(result[val])))
            build_information = COSMO_Run.find_cosmo_code_information(file)
            for k, v in build_information:
                print k
                self.timings.append((k, v))
            dycore_information = COSMO_Run.find_dycore_version_information(file)
            if not dycore_information:
                dycore_information = "None :("
            if dycore_information:
                self.timings.append(('Dycore', dycore_information))

    def __str__(self):
        res = self.name
        pad = "\n    "
        for (k, v) in self.timings:
            res += pad
            res += "{k}: {v}s".format(k=k, v=v)
        return res
    def __getitem__(self, name):
        items = [x[1] for x in self.timings if name == x[0] ]
        if len(items) is 0:
            return None
        if len(items) is 1:
            return items[0]
        return items
    def items(self):
        return [x[0] for x in self.timings]
    def __contains__(self, name):
        return name in self.items()
   
    @staticmethod
    def find_dycore_version_information(file, prefix="DYCORE C++/CUDA"):
        import re
        regex = re.compile(r'\s+(?P<value>.+)')
        for line in file:
            if prefix in line:
                match = regex.match(line)
                if match:
                    return match.group('value')
        return None
    @staticmethod
    def find_cosmo_code_information(file, 
            start=" ==== Code information used to build this binary ====",
            end=" ==== End of code information ===="):
        import re
        regex = re.compile(r'\s*(?P<name>[\w\s-]*[-\w]+)[\s\.]*:\s(?P<value>.+)')
        matches = []
        startpoint = False
        for line in file:
            if not startpoint:
                startpoint = line.startswith(start)
                if not startpoint:
                    continue
            if line.startswith(end):
                break
            match = regex.match(line)
            if match:
                idx = match.group('name')
                val = match.group('value')
                if val is None:
                    continue
                matches.append((idx, val))
        return matches

    @staticmethod
    def find_cosmo_benchmark(file, start=" END OF TIME STEPPING"):
        import re

        regex = re.compile(r'\s*(?P<id>\d+)\s+(?P<tag>\S+)\s+(?P<ncalls>\d+)\s+(?P<min>\d+\.*\d+)\s+(?P<max>\d+\.*\d+)\s+(?P<mean>\d+\.*\d+)')

        startpoint = not start
        matches = []
        for line in file:
            # Search for the startpoint
            if not startpoint:
                startpoint = line.startswith(start)
                # continue to next file if it is not found
                if not startpoint:
                    continue
            match = regex.match(line)
            if match:
                matches.append({
                    'id': match.group('id'),
                    'tag': match.group('tag'),
                    'ncalls': match.group('ncalls'),
                    'min': match.group('min'),
                    'max': match.group('max'),
                    'mean': match.group('mean')
                })
        return matches

    @staticmethod
    def parse_time(file, time_string="Start"):
        import re
        regex = re.compile(time_string+'[\S\s]+\s+(\d+)')
        for line in file:
            match = regex.search(line)
            if match:
                return match.group(1)

    @staticmethod
    def get_slurm_timing(file):
        start = COSMO_Run.parse_time(file, "Start")
        end = COSMO_Run.parse_time(file, "End")
        return float(end)-float(start)
