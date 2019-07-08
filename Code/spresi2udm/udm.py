"""Utility functions for generating UDM 5.0 (Brooklyn) files."""

__author__ = "Jarek Tomczak"
__email__ = "jarek.tomczak@pistoiaalliance.org"
__license__ = "MIT"

from ctutils import clean_reaction


def get_xml_declaration():
    """Return the XML declaration entity <?xml ...>."""
    return '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'


def format_udm_open(db_name, sequence_num, timestamp):
    """Return formatted opening <UDM ...> entity."""
    return '<UDM DATABASE="{}" SEQUENCE="{}" TIMESTAMP="{}">\n'.format(
        db_name, sequence_num, timestamp)

def format_udm_close():
    """Return the closing </UDM> entity."""
    return '</UDM>\n'


def format_version_entity(major, minor, revision):
    """Return formatted UDM_VERSION entity."""
    return ('  <UDM_VERSION MAJOR="{}" MINOR="{}" REVISION="{}"'
            ' VERSIONTEXT="{}.{}.{}"/>\n').format(
                major, minor, revision, major, minor, revision)


def format_citation(citation_id, citation):
    """Return formatted CITATION entity."""
    return '''    <CITATION ID="{}">
      <TYPE>{}</TYPE>
      <AUTHOR>{}</AUTHOR>
      <TITLE>{}</TITLE>
      <JOURNAL>{}</JOURNAL>
      <YEAR>{}</YEAR>
      <VOL>{}</VOL>
      <PAGE>{}</PAGE>
    </CITATION>
'''.format(citation_id,
           citation.type,
           citation.author,
           citation.title,
           citation.journal,
           citation.year,
           citation.volume,
           citation.page)


EMPTY_MOLFILE = '''
  rdf2udm_03051801012D

  0  0  0  0  0  0            999 V2000
M  END'''


def format_molecule(molecule_id, molfile, name):
    """Return formatted MOLECULE entity."""
    if not molfile:
        molfile = EMPTY_MOLFILE
    return '''    <MOLECULE ID="{}">
      <MOLSTRUCTURE><![CDATA[{}
]]></MOLSTRUCTURE>
      <NAME>{}</NAME>
    </MOLECULE>
'''.format(molecule_id, molfile, name)


def format_reaction(reaction, keep_mapping):
    """Return formatted REACTION entity."""
    if keep_mapping:
        rxn = reaction.rxn_block;
    else:
        rxn = clean_reaction(reaction.rxn_block)
    s = '''    <REACTION ID="{}">
      <RXNSTRUCTURE><![CDATA[{}
]]></RXNSTRUCTURE>
'''.format(reaction.reaction_id, rxn)
    for reactant_id in reaction.reactant_ids:
        s += '      <REACTANT_ID>' + str(reactant_id) + '</REACTANT_ID>\n'
    for product_id in reaction.product_ids:
        s += '      <PRODUCT_ID>' + str(product_id) + '</PRODUCT_ID>\n'
    s += '      <VARIATION CIT_ID="' + str(reaction.citation_id) + '">\n'
    s += '        <SOURCE>SPRESI</SOURCE>\n'
    for reactant_id in reaction.reactant_ids:
        s += '        <REACTANT ID="' + str(reactant_id) + '" />\n'
    for product_id in reaction.product_ids:
        s += '        <PRODUCT ID="' + str(product_id) + '">\n'
        s += '          <YIELD>' + str(reaction.reaction_yield) + '</YIELD>\n'
        s += '        </PRODUCT>\n'
    for catalyst_id in reaction.catalyst_ids:
        s += '        <CATALYST ID="' + str(catalyst_id) + '" />\n'
    for solvent_id in reaction.solvent_ids:
        s += '        <SOLVENT ID="' + str(solvent_id) + '" />\n'
    s += '      </VARIATION>\n'
    s += '    </REACTION>\n'
    return s
