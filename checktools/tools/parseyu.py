import re


class RowData:
    """Representation of a row in a data table."""

    def __init__(self, name, **data):
        self.name = name
        self.data = data
        for key, value in data.items():
            key = key.lower()
            if hasattr(self, key):
                raise ValueError('Cannot overwrite attribute {}.'.format(key))
            setattr(self, key, value)
        self._parent = None
        self._children = []

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, str(self))

    @property
    def children(self):
        return self._children

    @children.setter
    def children(self, value):
        if self._parent is not None:
            raise ValueError(
                    'Do not set children directly (use add_children).')

    @property
    def child_names(self):
        return [c.name for c in self.children]

    @property
    def child_dict(self):
        return {c.name: c for c in self.children}

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        if self._parent is not None:
            raise ValueError('Do not set parent of RowData multiple times.')
        if not isinstance(parent, RowData):
            raise ValueError('Parent must be an instance of RowData.')
        if self == parent.parent:
            raise ValueError('Circular relationship.')
        self._parent = parent

    @staticmethod
    def set_child_parent_relation(child, parent):
        child.parent = parent
        parent.add_child(child)

    def has_parent(self):
        return self.parent is not None

    def has_children(self):
        return bool(self.children)

    def get_child_depth(self, depth=0):
        max_depth = depth
        for child in self.children:
            d = child.get_child_depth(depth+1)
            if d > max_depth:
                max_depth = d
        return max_depth

    def get_parents(self, parents=[]):
        try:
            return self.parent.get_parents([self.parent] + parents)
        except AttributeError:
            return parents

    def add_child(self, child):
        if not isinstance(child, RowData):
            raise ValueError('Child must be an instance of RowData.')
        if self in child.children:
            raise ValueError('Circular relationship.')
        self._children.append(child)

    def as_dict(self):
        d = self.data
        d.update({c.name: c.as_dict() for c in self.children})
        return d

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        elif hasattr(self, key.lower()):
            return getattr(self, key.lower())
        elif key in self.child_names:
            return self.child_dict[key]
        else:
            raise IndexError('No element with name {} found.'.format(key))


class HirarchicalTableParser(object):
    """Parse hirarchical table data with a given format.

    Needed format is one name column separated from one to many data columns:
        NAME_COL DATA_COL ...

    """
    def __init__(self, data_col_names, subcategory_indention='\t', ):
        self.data_col_names = data_col_names
        self.col_names = ['name'] + data_col_names
        self.subcategory_indention = subcategory_indention
        self.row_regex = re.compile(
                self.get_row_regex_str(len(data_col_names)))
        self.rows = []

    @property
    def row_names(self):
        """Return the names of all root rows (rows without parents)."""
        return [r.name for r in self.rows if r.parent is None]

    @property
    def row_dict(self):
        """Return dictionary of all root rows (rows without parents)."""
        return {r.name: r for r in self.rows if r.parent is None}

    def get_name_col_regex_str(self):
        """Return partial regex for the column name."""
        return r'^(\s*.*?)'

    def get_data_col_regex_str(self):
        """Return partial regex for the column data."""
        return r'(\d+\.\d*)\s*'

    def get_row_regex_str(self, N_data_cols):
        """Combine partial regex to a complete regex over all columns."""
        name_col = self.get_name_col_regex_str()
        data_col = self.get_data_col_regex_str()
        return name_col + N_data_cols * data_col

    def parse_lines(self, lines):
        """Parse lines and add RowData instances to the row attribute."""
        row_tree = None
        for line in lines:
            if not line:
                continue
            m = self.row_regex.search(line)

            if m is None:
                continue
            groups = list(m.groups())
            name_raw = str(groups.pop(0))
            name = name_raw.strip()
            name = re.sub('\s+', ' ', name)
            data = [float(v.strip()) for v in groups]
            row = RowData(
                    name, **{n: d for n, d in zip(self.data_col_names, data)})
            self.rows.append(row)

            ind = self.subcategory_indention
            depth = int((len(name_raw)-len(name_raw.lstrip(ind)))/len(ind))

            if row_tree is None:
                row_tree = [row]
            elif len(row_tree) < depth:
                raise ValueError(
                        'A hirarchical level was skipped! Found element of '
                        'depth {}. However parent element is of depth '
                        '{}.'.format(depth, len(row_tree)-1))
            elif len(row_tree) >= depth:
                row_tree = row_tree[:depth]
                try:
                    parent_row = row_tree[-1]
                    RowData.set_child_parent_relation(row, parent_row)
                except IndexError:
                    pass
                row_tree += [row]

    def as_dict(self):
        d = {name: self.row_dict[name].as_dict() for name in self.row_names}
        return d

    def __getitem__(self, key):
        if key in self.row_names:
            return self.row_dict[key]
        else:
            raise IndexError('No element with name {} found.'.format(key))


def get_yutiming_header_data(f, header_start=7, header_end=9):
    """Parse given YUTIMING file and return its header data as a dictionary."""
    with open(f, 'r') as file_:
        lines = file_.readlines()
        regex = re.compile(r'^(\s*.*?)(\d+\.\d*)\s*')
        d = {}
        for line in lines[header_start-1:header_end]:
            m = regex.search(line)
            if m is not None:
                g = m.groups()
                key = str(g[0]).strip()
                key = key.rstrip(':')
                value = float(g[1])
                d[key] = value
        return d


def get_yutiming_body_data(f):
    """Parse given YUTIMING file and return dictionary of its main data."""
    htb = HirarchicalTableParser(
            data_col_names=['min', 'avg', 'max', 'total'],
            subcategory_indention=' '*2)
    with open(f, 'r') as file_:
        htb.parse_lines(file_.readlines())
    return htb.as_dict()

def read_file(folder, filename):
    from os import path
    file = open(path.join(folder, filename))
    return file.readlines()

class COSMO_Run_yu:
    def __init__(self, folder, name, yutimings="YUTIMING", cosmolog="exe.log", slurmlog="cosmo_benchmark.out"):
        self.name = name
        self.timings = []
        self.metadata = {}
        if slurmlog:
            file = read_file(folder, slurmlog)
            self.timings.append(("total", float(COSMO_Run_yu.get_slurm_timing(file))))

        if cosmolog:
            file = read_file(folder, cosmolog)
            build_information = COSMO_Run_yu.find_cosmo_code_information(file)
            for k, v in build_information:
                self.metadata.update({k: v})
            dycore_information = COSMO_Run_yu.find_dycore_version_information(file)
            if not dycore_information:
                dycore_information = "None :("
            if dycore_information:
                self.metadata.update({'Dycore': dycore_information})

        if yutimings:
            file = read_file(folder, yutimings)
            header = get_yutiming_header_data(yutimings)
            self.benchmark_metadata = header
            val = header["Time for the setup of the model"]
            self.timings.append(("setup", val))

            body = get_yutiming_body_data(yutimings)
            self.benchmark_metadata = body
            val = 0
            dyn = ["Dyn. Computations", "Cpp dycore step", "Cpp dycore copy in", "Cpp dycore copy out"]
            for result in dyn:
                val = body[result]["max"] + val
            self.timings.append(("dynamics max", val))

            val = body["Phy. Computations"]["max"]
            self.timings.append(("physics max", val))

            val = body["Add. Computations"]["max"]
            self.timings.append(("add.comp. max", val))

            val = 0
            io = ["Input", "Output"]
            for result in io:
                val = body[result]["max"] + val
                if result is "Input":
                  val = body[result]["read data"]["max"] + val
                  val = body[result]["meta data"]["max"] + val
                  val = body[result]["computations I"]["max"] + val
                  val = body[result]["distribute data"]["max"] + val
                if result is "Output":
                  val = body[result]["computations O"]["max"] + val
                  val = body[result]["meta data"]["max"] + val
                  val = body[result]["write data"]["max"] + val
                  val = body[result]["gather data"]["max"] + val
            self.timings.append(("io max", val))

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
    def parse_time(file, time_string="Start"):
        import re
        regex = re.compile(time_string+'[\S\s]+\s+(\d+)')
        for line in file:
            match = regex.search(line)
            if match:
                return match.group(1)

    @staticmethod
    def get_slurm_timing(file):
        start = COSMO_Run_yu.parse_time(file, "Start")
        end = COSMO_Run_yu.parse_time(file, "End")
        return float(end)-float(start)
