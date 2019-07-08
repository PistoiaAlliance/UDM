"""Utility functions for processing connection tables and related data."""


def clean_atom(atom_line):
    """Removes reaction-specific properties (e.g. atom-atom mapping) from the
atom_line and returns the updated line."""
    return atom_line[:60] + '  0  0  0'


def clean_bond(bond_line):
    """Removes reaction center status from the bond_line and returns the
updated line."""
    return bond_line[:18] + '  0'


def clean_molecule(molfile):
    """Removes reaction information from the specified molfile and returns
the cleaned-up version."""
    counts_line = molfile[3]
    num_atoms = int(counts_line[:3])
    num_bonds = int(counts_line[3:6])
    clean_mol = []
    clean_mol[:4] = molfile[:4]
    for atom_line in molfile[4:num_atoms+4]:
        clean_mol.append(clean_atom(atom_line))
    for bond_line in molfile[num_atoms+4:num_atoms+num_bonds+4]:
        clean_mol.append(clean_bond(bond_line))
    m_len = len(molfile)
    clean_mol[num_atoms+num_bonds+4:m_len] = molfile[num_atoms+num_bonds+4:m_len]
    return clean_mol



def find_end_of_molfile(rxn, start):
    end = start + 1
    while rxn[end] != 'M  END':
        end += 1
    return end + 1  # Include "M  END"


def clean_reaction(rxn_block):
    """Remove atom-atom mappings and reaction centres from the given RXN
block and return the cleaned version."""
    reaction = rxn_block.split('\n')
    clean_reaction = []
    clean_reaction[:5] = reaction[:5]
    line = reaction[4]
    num_reactants = int(line[:3])
    num_products = int(line[3:6])
    start_line = 5
    for n in range(0, num_reactants + num_products):
        clean_reaction.append(reaction[start_line])  # $MOL line
        # print('>>', reaction[start_line], num_reactants, num_products)
        start_line += 1
        end_line = find_end_of_molfile(reaction, start_line)
        clean_reaction.extend(clean_molecule(reaction[start_line:end_line]))
        start_line = end_line
        # print(len(clean_reaction))    
    return '\n'.join(clean_reaction)
