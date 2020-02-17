"""Convert SPRESI RD file to UDM."""

__author__ = "Jarek Tomczak"
__email__ = "jarek.tomczak@pistoiaalliance.org"
__license__ = "MIT"

import datetime
import re
import sys
from collections import namedtuple
from ctutils import clean_molecule
from rdfutils import FileFormatException, rdfile_reader
import udm


# We represent citations as named tuples rather than objects so they can be
# used as keys in a dictionary used for their de-duplication.
Citation = namedtuple('Citation',
                      ['author', 'title', 'journal', 'year', 'volume', 'page', 'type'])


# Dictionaries and list used for compound registration and de-duplication.
compound_registry = {}
compound_names = {}
anonymous_compounds = []


def register_molecule(molfile, name, reaction_id):
    """Register a molecule specified by its molfile and name and return
identifier.  The following rules are applied:
 1. If the molecular structure is known (molfile not empty), it is used for
    registration and de-duplication, otherwise
 2. If the name of the molecule is not empty, it is used for de-duplication,
    otherwise
 3. A new anonymous molecule is registered with a unique ID for each empty
    structure with no name."""
    try:
        if molfile:
            cleaned_molfile = '\n'.join(clean_molecule(molfile))
            if cleaned_molfile in compound_registry:
                return compound_registry[cleaned_molfile][0]
            c_id = len(compound_registry) + len(compound_names) + len(anonymous_compounds) + 1
            cleaned_name = name
            if name:
                cleaned_name = name.strip()
            compound_registry[cleaned_molfile] = (c_id, cleaned_name)
            return c_id
        elif name:
            cleaned_name = name.strip()
            if cleaned_name in compound_names:
                return compound_names[cleaned_name]
            c_id = len(compound_registry) + len(compound_names) + len(anonymous_compounds) + 1
            compound_names[cleaned_name] = c_id
            return c_id
        else:
            c_id = len(compound_registry) + len(compound_names) + len(anonymous_compounds) + 1
            anonymous_compounds.append(c_id)
            return c_id
    except Exception as ex:
        print(reaction_id, molfile)
        raise ex


CATALYST_RE = re.compile(r'RXN:VARIATION:STEPNO:CATALYST\((?P<N>[0-9])\):MOL:MOLSTRUCTURE')
SOLVENT_RE = re.compile(r'RXN:VARIATION:STEPNO:SOLVENT\((?P<N>[0-9])\):MOL:MOLSTRUCTURE')


def get_catalysts(reaction):
    """Return catalysts involved in the specified reaction."""
    for df in reaction.data_fields:
        if CATALYST_RE.match(df):
            n = CATALYST_RE.search(df).group('N')
            name_field = 'RXN:VARIATION:STEPNO:CATALYST(' + n + '):MOL:SYMBOL'
            if name_field in reaction.data_fields:
                name = reaction.data_fields[name_field]
            else:
                name = ''
            yield reaction.data_fields[df], name, n


def get_solvents(reaction):
    """Return solvents involved in the specified reaction."""
    for df in reaction.data_fields:
        if SOLVENT_RE.match(df):
            n = SOLVENT_RE.search(df).group('N')
            name_field = 'RXN:VARIATION:STEPNO:SOLVENT(' + n + '):MOL:SYMBOL'
            if name_field in reaction.data_fields:
                name = reaction.data_fields[name_field]
            else:
                name = ''
            yield reaction.data_fields[df], name, n


YIELD_RE = re.compile(r'(?P<M>[0-9\.]+)-[0-9\.]+')

def get_yield(reaction):
    """Parse and return the yield of the specified reaction."""
    yld = reaction.data_fields.get('RXN:VARIATION:PRODUCT:YIELD', None)
    if yld:
        # Yield value is min-max in SPRESI, but UDM expects a single value.
        if YIELD_RE.match(yld):
            yld = YIELD_RE.search(yld).group('M')
    return yld


citations = {}


def text_to_xml(text):
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def get_citation(reaction):
    """Parse and return the citation associated with the specified reaction."""
    df = reaction.data_fields
    title = text_to_xml(df.get('RXN:VARIATION:LITREF:TITLE', ''))
    return Citation(df.get('RXN:VARIATION:LITREF:AUTHOR', ''),        # author
                    title,                                            # title
                    df.get('RXN:VARIATION:LITREF:JOURNAL_JRNL', ''),  # journal
                    df.get('RXN:VARIATION:LITREF:JOURNAL_YEAR', ''),  # year
                    df.get('RXN:VARIATION:LITREF:JOURNAL_VOL.', ''),  # volume
                    df.get('RXN:VARIATION:LITREF:JOURNAL_PG.', ''),   # page
                    df.get('RXN:VARIATION:LITREF:TYPE', ''))          # type


def register_citation(citation):
    """Register the citation and return its unique identifier."""
    if citation in citations:
        return citations[citation]
    cit_id = len(citations) + 1
    citations[citation] = cit_id
    return cit_id


def format_rxn_header(reaction_id):
    """Returns string containing four-line RXN header."""
    #               <-A6-><---A9--><---A12----><--I7->
    #               IIIIIIPPPPPPPPPMMDDYYYYHHmmRRRRRRR
    return '$RXN\n\n      INFOCHEM             {:<7}\n'.format(reaction_id)


def format_rxn_block(reaction):
    """Generate and return RXN block for the given reaction."""
    s = format_rxn_header(reaction.id)
    s += '\n{:>3d}{:>3d}'.format(len(reaction.reactants), len(reaction.products))
    for reactant in reaction.reactants:
        s += '\n$MOL\n' + '\n'.join(reactant)
    for product in reaction.products:
        s += '\n$MOL\n' + '\n'.join(product)
    return s


ReactionEntity = namedtuple('ReactionEntity', ['reaction_id', 'reactant_ids',
                                               'product_ids', 'catalyst_ids',
                                               'solvent_ids', 'rxn_block',
                                               'citation_id', 'reaction_yield'])


def parse_spresi_reaction(reaction):
    """Parse the specified reaction from a SPRESI RD file, extract UDM-relevant
data and return them a new instance of ReactionEntity."""
    reactant_ids = [register_molecule(r, '', reaction.id) for r in reaction.reactants]
    product_ids = [register_molecule(p, '', reaction.id) for p in reaction.products]
    catalyst_ids = {}  # Key - the catalyst number, value - molecule ID.
    solvent_ids = {}  # Key - the solvent number, value - molecule ID.
    for molfile, name, n in get_catalysts(reaction):
        catalyst_ids[n] = register_molecule(molfile, name, reaction.id)
    for molfile, name, n in get_solvents(reaction):
        solvent_ids[n] = register_molecule(molfile, name, reaction.id)
    citation_id = register_citation(get_citation(reaction))
    rxn_block = format_rxn_block(reaction)
    reaction_yield = get_yield(reaction)

    return ReactionEntity(reaction.id, reactant_ids, product_ids, catalyst_ids,
                          solvent_ids, rxn_block, citation_id, reaction_yield)


def format_timestamp(date_time, time_zone):
    """Format and return a timestamp for the the specified date and time."""
    # FIXME Improve formatting of the time zone.
    return '{:%Y-%m-%dT%H:%M:%S}{}'.format(date_time, time_zone)


def write_udm_legal(fout):
    fout.write('''    <LEGAL>
      <PRODUCER>InfoChem GmbH</PRODUCER>
      <TITLE>Sample SPRESI dataset</TITLE>
      <LICENSE href="https://creativecommons.org/licenses/by-nc-sa/4.0/">
        Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
        (CC BY-NC-SA 4.0)
      </LICENSE>
      <COPYRIGHT href="http://www.infochem.de">
        <TEXT>Copyright (c) 2020 InfoChem</TEXT>
        <OWNER>InfoChem</OWNER>
        <YEAR>2020</YEAR>
      </COPYRIGHT>
    </LEGAL>
''')


def write_udm_citations(fout):
    """Write CITATIONS entity to the fout stream."""
    fout.write('  <CITATIONS>\n')
    for citation, citation_id in citations.items():
        fout.write(udm.format_citation(citation_id, citation))
    fout.write('  </CITATIONS>\n')


def write_udm_molecules(fout):
    """Write MOLECULES entity to the fout stream."""
    fout.write('  <MOLECULES>\n')
    for molfile, mol_info in compound_registry.items():
        molecule_id, name = mol_info
        fout.write(udm.format_molecule(molecule_id, molfile, name))
    for name, molecule_id in compound_names.items():
        fout.write(udm.format_molecule(molecule_id, '', name))
    for molecule_id in anonymous_compounds:
        fout.write(udm.format_molecule(molecule_id, '', ''))
    fout.write('  </MOLECULES>\n')


def write_udm_reactions(fout, reaction_entities):
    """Write REACTIONS entity to the fout stream."""
    fout.write('  <REACTIONS>\n')
    num_reactions = 0
    for reaction in reaction_entities:
        num_reactions += 1
        fout.write(udm.format_reaction(reaction, num_reactions <= 100))
    fout.write('  </REACTIONS>\n')


def write_udm_file(filename, reaction_entities):
    """Write filename UDM file for the given set of reactions."""
    with open(filename, 'wt') as fout:
        fout.write(udm.get_xml_declaration())
        timestamp = format_timestamp(datetime.datetime(2020, 1, 29, 13, 34, 0), '+01:00')
        fout.write(udm.format_udm_open('SPRESI', 1, timestamp))
        fout.write(udm.format_version_entity(6, 0, 0))
        write_udm_legal(fout)
        write_udm_citations(fout)
        write_udm_molecules(fout)
        write_udm_reactions(fout, reaction_entities)
        fout.write(udm.format_udm_close())


def main():
    """Main function for conversion of SPRESI RD file to UDM."""
    rd_filename = 'spresi-sample.rdf' # Default input file if none specified.
    udm_filename = 'spresi.xml'       # Default output file  if none specified.

    num_args = len(sys.argv)
    if num_args >= 2:
        udm_filename = sys.argv[2]
    if num_args >= 1:
        rd_filename = sys.argv[1]

    reaction_entities = []
    try:
        # Read all the reactions from the input file, register the involved
        # molecules and citations and store all the UDM-relevant information
        # in reactions_entities.
        num_reactions = 0
        for reaction in rdfile_reader(rd_filename):
            # We export only first 10K reactions from the SPRESI RD file provided
            # by InfoChem.
            num_reactions += 1
            if num_reactions > 10000:
                break;
            reaction_entities.append(parse_spresi_reaction(reaction))

        write_udm_file(udm_filename, reaction_entities)
    except FileExistsError as fee:
        print('error: cannot read file ' + rd_filename, fee)
    except FileFormatException as ffe:
        print('error: cannot parse input file line ' + str(ffe.line_no) + ':', ffe)


if __name__ == '__main__':
    main()
