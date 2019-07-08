"""Functions and classes for processing RD files."""

__author__ = "Jarek Tomczak"
__email__ = "jarek.tomczak@pistoiaalliance.org"
__license__ = "MIT"

import re
from enum import Enum


class Reaction():
    """Class representing single chemical reaction."""
    def __init__(self, id, name, reactants, products, data_fields):
        self.id = id
        self.name = name
        self.reactants = reactants
        self.products = products
        self.data_fields = data_fields


class FileFormatException(Exception):
    """Exception raised for invalid format of input file."""
    def __init__(self, message, line_no):
        # Call the base class constructor with the parameters it needs.
        super().__init__(message)
        # Custom attribute.
        self.line_no = line_no


class LineReader():
    """Utility class for reading line-oriented text files."""

    def __init__(self, filename):
        self.filename = filename
        self.stream = open(filename, 'rt', newline='', encoding='utf-8')
        self.line = None        # Stores the last line read from the stream.
        self.line_no = 0        # The number of the last read line.
        self.saved_line = None  # If not None then it stores the line pushed back by unget_line().
        self.eof = False        # True if the end of the stream has been reached.

    def get_line(self):
        """Reads and returns the next input line from the stream associated
    with the line reader."""
        if self.eof:
            return None
        if self.saved_line:
            self.line = self.saved_line
            self.saved_line = None
        else:
            l = self.stream.readline()
            if l:
                self.line = l.rstrip()
                self.eof = False
            else:
                self.line = None
                self.eof = True
        self.line_no += 1
        return self.line

    def unget_line(self):
        """Pushes back the last read line, so the next call to get_line() will
    return the same line.  Only one last read line can be pushed back."""
        if self.line:
            self.line_no -= 1
            self.saved_line = self.line
            self.line = None
            self.eof = False

    def close(self):
        """Close the stream associated with the line reader."""
        self.stream.close()


class CTFileVersion(Enum):
    """Enumeration representing CTFile formats."""
    V2000 = 2000
    V3000 = 3000


# Compiled regular expressions
MR_IDENTIFIER_RE = re.compile(r'\$RFMT \$RIREG (?P<ID>\d+)')


def rdfile_reader(filename):
    """Generator function returning individual reactions from the specified
RD file."""
    lr = LineReader(filename)
    read_rdf_header(lr)
    keep_reading = True
    while keep_reading:
        reaction, keep_reading = read_reaction(lr)
        yield reaction
    lr.close()


def read_reaction(lr):
    """Reads and returns a single reaction from an RD file associated with the
lr line reader."""
    r_id = read_rfmt_line(lr)
    format_version, reaction_name = read_rxn_header(lr)
    reactants, products = read_rxn_block_v2000(lr)
    data_fields = {}
    field_name = None
    field_value = True
    while True:
        field_name, field_value = read_rdf_data_field(lr)
        if not field_name:
            break
        else:
            data_fields[field_name] = field_value
        # print('field_name', field_name)
    reaction = Reaction(r_id, reaction_name, reactants, products, data_fields)
    # field_value will contain True if there is another reaction to be read
    # or False if end of file has been reached.
    return reaction, field_value


def read_rdf_header(lr):
    """Reads two lines of the RD file header and raises the FileFormatException
if any of them doesn't have a valid format."""

    # Check the first header line.
    line = lr.get_line()
    if line != '$RDFILE 1':
        raise FileFormatException('invalid first header line of RD file', 1)

    # Check the second header line, expected format: "$DATM mm/dd/yy hh:mm".
    line = lr.get_line()
    if not re.match(r'\$DATM \d\d/\d\d/\d\d \d\d:\d\d', line):
        raise FileFormatException('invalid second header line of RD file', 2)


def read_rfmt_line(lr):
    """Reads a molecule or reaction identifier which defines a start of each
complete record in an RDfile.  Returns two values: the extracted identifier
and the number of lines read so far."""
    line = lr.get_line()
    if not MR_IDENTIFIER_RE.match(line):
        raise FileFormatException('invalid molecule/reaction identifier line', lr.line_no)
    mr_id = MR_IDENTIFIER_RE.search(line).group('ID')
    return mr_id


def read_rxn_header(lr):
    """Reads a single RXN block (file) containing structural data for the
reactants and products of a reaction."""

    # Init values of the returned variables.
    format_version = CTFileVersion.V2000

    # Get and process the first RXN header line.
    line = lr.get_line()
    if line == '$RXN V3000':
        format_version = CTFileVersion.V3000
    elif line != '$RXN':
        raise FileFormatException('invalid first line of RXN header block: ' + lr.line, lr.line_no)

    # Read the second header line - the reaction name (usually empty).
    reaction_name = lr.get_line()

    # Read the third header line - user's initials(I), program name and version(P),
    # date/time(M/D/Y,H:m) and reaction registry number(R). This line has the format:
    #   IIIIIIPPPPPPPPPMMDDYYYYHHmmRRRRRRR
    #   <-A6-><---A9--><---A12----><--I7-> )
    #
    # FIXME Implement parsing of the third header line.
    lr.get_line()

    # Skip the fourth header line (comment), usually empty.
    lr.get_line()

    return format_version, reaction_name


def read_rxn_block_v2000(lr):
    """Reads an RXN block (reactants and products) following the RXN header
and returns the read molecules."""
    num_reactants, num_products = read_rxn_counts_line_v2000(lr)
    reactants = read_n_molfiles_v2000(lr, num_reactants)
    products = read_n_molfiles_v2000(lr, num_products)
    return reactants, products


def read_rxn_counts_line_v2000(lr):
    """Reads the next line from the lr line reader which is expected to
contain the numbers of reactants and products in the 'rrrppp' format and
returns the numbers."""
    line = lr.get_line()
    num_reactants = int(line[:3])
    num_products = int(line[3:6])
    return num_reactants, num_products


def read_n_molfiles_v2000(lr, n):
    """Reads n molfiles from the lr line reader and return them as a tuple."""
    molfiles = []
    for i in range(n):
        line = lr.get_line()
        if line != '$MOL':
            raise FileFormatException('invalid molfile delimited', lr.line_no)
        m = read_molfile_v2000(lr)
        molfiles.append(m)
    return tuple(molfiles)


def read_molfile_v2000(lr):
    """Reads a single V2000 molfile and returns it as a tuple containing
individual lines."""
    molfile = []
    line = ''
    while not lr.eof and line != 'M  END' and line[:6] != '$DTYPE':
        line = lr.get_line()
        # We need to deal with empty molfiles after $DATUM $MFMT or ones
        # without "M  END".
        if line and line[:6] == '$DTYPE':
            break
        molfile.append(line)
    if line[:6] == '$DTYPE':
        lr.unget_line()
    return tuple(molfile)


def read_rdf_data_field(lr):
    """Read and return a single data field as a (name, value) tuple.
If there are no more data fields available, but a new data record
following, the function returns (None, True).  On the end of file
the function returns (None, False)."""
    # Read data field name.
    line = lr.get_line()
    if not line:
        return None, False       # No more data fields, end of file.
    elif line[:5] == '$RFMT':
        lr.unget_line()
        return None, True      # No more data fields, new reaction record.
    if line[:6] != '$DTYPE':
        raise FileFormatException('missing $DTYPE line', lr.line_no)
    field_name = line[7:]
    if not field_name:
        raise FileFormatException('missing field name', lr.line_no)

    # Read data field value
    line = lr.get_line()
    if not line or line[:6] != '$DATUM':
        raise FileFormatException('missing $DATUM line', lr.line_no)
    field_value = line[7:]
    if contains_embedded_molfile(field_value):
        field_value = read_molfile_v2000(lr)
    elif ends_with_plus(field_value, True):
        field_value = read_rdf_field_value(lr, field_value)

    return field_name, field_value


def contains_embedded_molfile(field_value):
    """Returns True if the RD file $DATUM field value contains an embedded
molfile, otherwise returns False."""
    return field_value == '$MFMT'


def read_rdf_field_value(lr, field_value):
    """Read and return a single data field value or None on end of file."""
    new_paragraph = False
    l = len(field_value)
    val = field_value[:l-1]
    while True:
        line = lr.get_line()
        if line:
            if line[:6] == '$DTYPE':
                # Next date field - complete processing of the current one.
                lr.unget_line()
                return val
            elif line[:5] == '$RFMT':
                lr.unget_line()
                return val
            elif ends_with_plus(line, False):
                if new_paragraph:
                    val += '\n\n'
                    new_paragraph = False
                l = len(line)
                val += line[:l-1]
            else:
                if new_paragraph:
                    val += '\n\n'
                    new_paragraph = False
                val += line
        else:
            if lr.eof:
                return val # None
            else:
                # Empty line usually separates paragraph of texts, but it
                # can be also a separator before the next $DTYPE or trailing
                # newline at the end of the file.
                new_paragraph = True


def ends_with_plus(s, datum_line):
    """Returns True if the last character of s is a plus (+) marking string
concatenation, otherwise returns False."""
    l = len(s)
    return (l > 0) and (s[l - 1] == '+') and \
        ((datum_line and l >= 72) or (not datum_line and l >= 81))
