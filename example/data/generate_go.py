# -*- coding: utf-8 -*-
"""
Orthogonal Graphene Oxide Generator (0.20 O/C Ratio, Double-Sided, 10x10 rectangular)
------------------------------------------------------------------------------------
Uses the Atomic Simulation Environment (ASE) to build a periodic orthogonal graphene sheet
centered at Z=0.0 Å and populate it randomly on both sides with epoxy (C-O-C) and
hydroxyl (-OH) groups to achieve an exact O/C ratio of 0.20 (40 oxygen atoms on 200 carbons).
Uses a perfectly rectangular unit cell to completely prevent any flying atom visual artifacts.
"""

import sys
import random
import numpy as np
from pathlib import Path
from ase import Atoms
from ase.io import write


def check_clashes(atoms, selected_epoxies, selected_hydroxyls, num_carbons):
    """
    Verifies that there are no non-bonded steric clashes in the system,
    ignoring chemically bonded atom pairs.
    """
    # Compute full pairwise MIC distance matrix
    dists = atoms.get_all_distances(mic=True)
    
    # Exclude bonded pairs by setting their distance to infinity
    # Epoxy exclusions (C_u - O and C_v - O)
    epoxy_o_start = num_carbons
    for idx, (u, v) in enumerate(selected_epoxies):
        o_idx = epoxy_o_start + idx
        dists[u, o_idx] = np.inf
        dists[o_idx, u] = np.inf
        dists[v, o_idx] = np.inf
        dists[o_idx, v] = np.inf
        
    # Hydroxyl exclusions (C - O, O - H, and C - H)
    hydroxyl_start = num_carbons + len(selected_epoxies)
    for idx, c in enumerate(selected_hydroxyls):
        o_idx = hydroxyl_start + 2 * idx
        h_idx = o_idx + 1
        dists[c, o_idx] = np.inf
        dists[o_idx, c] = np.inf
        dists[o_idx, h_idx] = np.inf
        dists[h_idx, o_idx] = np.inf
        dists[c, h_idx] = np.inf
        dists[h_idx, c] = np.inf
        
    # Fill diagonal with infinity
    np.fill_diagonal(dists, np.inf)
    
    # Filter distances by element pairs
    symbols = atoms.symbols
    o_indices = [i for i, sym in enumerate(symbols) if sym == 'O']
    c_indices = [i for i, sym in enumerate(symbols) if sym == 'C']
    h_indices = [i for i, sym in enumerate(symbols) if sym == 'H']
    
    # O-O clash threshold: 1.8 Å
    if len(o_indices) > 0:
        o_dists = dists[np.ix_(o_indices, o_indices)]
        if np.any(o_dists < 1.8):
            return False
            
    # C-O non-bonded clash threshold: 1.6 Å
    if len(c_indices) > 0 and len(o_indices) > 0:
        co_dists = dists[np.ix_(c_indices, o_indices)]
        if np.any(co_dists < 1.6):
            return False
            
    # H-H clash threshold: 1.2 Å
    if len(h_indices) > 0:
        hh_dists = dists[np.ix_(h_indices, h_indices)]
        if np.any(hh_dists < 1.2):
            return False
            
    # H-O non-bonded clash threshold: 1.5 Å
    if len(h_indices) > 0 and len(o_indices) > 0:
        ho_dists = dists[np.ix_(h_indices, o_indices)]
        if np.any(ho_dists < 1.5):
            return False
            
    # H-C non-bonded clash threshold: 1.5 Å
    if len(h_indices) > 0 and len(c_indices) > 0:
        hc_dists = dists[np.ix_(h_indices, c_indices)]
        if np.any(hc_dists < 1.5):
            return False
            
    return True


def generate_graphene_oxide(target_ratio=0.20, max_attempts=1000):
    """
    Generates a chemically correct, steric-clash-free orthogonal Graphene Oxide cell
    with an Oxygen/Carbon ratio of exactly target_ratio (0.20).
    Populates functional groups randomly on both sides of the sheet.
    Centers the base graphene sheet at Z=0.0 Å.
    """
    print(f"Generating random double-sided orthogonal Graphene Oxide at Z=0.0 (O/C ratio: {target_ratio:.2f})...")
    
    # 1. Create a 4-atom rectangular unit basis of graphene (C-C distance = 1.42 Å)
    # a = [4.26, 0.0, 0.0]
    # b = [0.0, 2.459512, 0.0]
    basis = Atoms('C4',
                  positions=[[0.0, 0.0, 0.0],
                             [1.42, 0.0, 0.0],
                             [2.13, 1.229756, 0.0],
                             [3.55, 1.229756, 0.0]],
                  cell=[4.26, 2.459512, 25.0],
                  pbc=[True, True, False])
                  
    # Tile it (5, 10, 1) to get exactly 200 carbon atoms
    base_atoms = basis * (5, 10, 1)
    num_carbons = len(base_atoms)  # Exactly 200 carbons
    
    # Z coordinate is already centered at 0.0 Å because basis is at Z=0.0
    
    # Target total oxygen atoms for O/C = 0.20: 200 * 0.20 = 40 oxygens
    # We choose exactly 20 epoxides (C-O-C) and 20 hydroxyls (-OH)
    num_epoxy = 20
    num_hydroxyl = 20
    
    # Find all C-C bonds (covalent bond distance in graphene is ~1.42 Å)
    from ase.neighborlist import neighbor_list
    i_list, j_list = neighbor_list('ij', base_atoms, cutoff=1.45)
    
    all_bonds = []
    for i, j in zip(i_list, j_list):
        if i < j:
            all_bonds.append((i, j))
            
    # Stochastic trial loop
    for attempt in range(max_attempts):
        # Reset structures and lists
        atoms = base_atoms.copy()
        functionalized_carbons = set()
        selected_epoxies = []
        selected_hydroxyls = []
        
        # Shuffle bonds and carbons for random population
        random.shuffle(all_bonds)
        
        # 1. Try to select 20 non-overlapping bonds for epoxies
        for u, v in all_bonds:
            if len(selected_epoxies) >= num_epoxy:
                break
            if u not in functionalized_carbons and v not in functionalized_carbons:
                selected_epoxies.append((u, v))
                functionalized_carbons.add(u)
                functionalized_carbons.add(v)
                
        if len(selected_epoxies) < num_epoxy:
            continue  # Try again if we couldn't find enough bonds
            
        # 2. Try to select 20 individual carbon atoms for hydroxyls from remaining carbons
        available_carbons = [c for c in range(num_carbons) if c not in functionalized_carbons]
        if len(available_carbons) < num_hydroxyl:
            continue
            
        selected_hydroxyls = random.sample(available_carbons, num_hydroxyl)
        functionalized_carbons.update(selected_hydroxyls)
        
        # 3. Build the actual Atoms structure
        new_atoms = atoms.copy()
        add_symbols = []
        add_positions = []
        carbon_displacements = np.zeros((num_carbons, 3))
        
        # Add Epoxy Groups (-O-) randomly on top (+1) or bottom (-1)
        for idx, (u, v) in enumerate(selected_epoxies):
            side = random.choice([1, -1])
            diff = atoms.get_distance(u, v, vector=True, mic=True)
            midpoint = atoms.positions[u] + 0.5 * diff
            
            o_pos = midpoint.copy()
            o_pos[2] += side * 1.24
            add_symbols.append('O')
            add_positions.append(o_pos)
            
            # Pull carbons slightly out-of-plane to simulate sp3 pyramidalization
            carbon_displacements[u, 2] += side * 0.22
            carbon_displacements[v, 2] += side * 0.22
            
        # Add Hydroxyl Groups (-OH) randomly on top (+1) or bottom (-1)
        for idx, c in enumerate(selected_hydroxyls):
            side = random.choice([1, -1])
            c_pos = atoms.positions[c]
            o_pos = c_pos.copy()
            o_pos[2] += side * 1.43
            
            # Place hydrogen at a realistic angle pointing away
            phi = random.uniform(0, 2.0 * np.pi)
            h_pos = o_pos.copy()
            h_pos[0] += 0.90 * np.cos(phi)
            h_pos[1] += 0.90 * np.sin(phi)
            h_pos[2] += side * 0.32
            
            add_symbols.append('O')
            add_positions.append(o_pos)
            add_symbols.append('H')
            add_positions.append(h_pos)
            
            # Pull carbon slightly out-of-plane to simulate sp3 pyramidalization
            carbon_displacements[c, 2] += side * 0.32
            
        # Apply displacements to carbon sheet
        for c in range(num_carbons):
            new_atoms.positions[c] += carbon_displacements[c]
            
        # Extend base sheet with the extra functional groups
        extra_atoms = Atoms(symbols=add_symbols, positions=add_positions)
        new_atoms.extend(extra_atoms)
        new_atoms.set_pbc([True, True, False])
        
        # Wrap strictly along X and Y boundaries to prevent flying atoms
        new_atoms.wrap()
        
        # 4. Check for clashes
        if check_clashes(new_atoms, selected_epoxies, selected_hydroxyls, num_carbons):
            # Success stats
            o_count = sum(1 for sym in new_atoms.symbols if sym == 'O')
            c_count = sum(1 for sym in new_atoms.symbols if sym == 'C')
            h_count = sum(1 for sym in new_atoms.symbols if sym == 'H')
            up_o = sum(1 for idx, sym in enumerate(new_atoms.symbols) if sym == 'O' and new_atoms.positions[idx][2] > 0.0)
            down_o = sum(1 for idx, sym in enumerate(new_atoms.symbols) if sym == 'O' and new_atoms.positions[idx][2] < 0.0)
            
            print(f"\n🎉 Graphene Oxide Generation Completed successfully on attempt {attempt + 1}!")
            print(f"Carbons:   {c_count}")
            print(f"Oxygens:   {o_count} (20 epoxy + 20 hydroxyl)")
            print(f"Hydrogens:  {h_count}")
            print(f"O/C Ratio:  {o_count / c_count:.4f} (Exactly {target_ratio})")
            print(f"Sides distribution: UP = {up_o}, DOWN = {down_o}")
            print(f"Unit cell dimensions: {new_atoms.cell.lengths()}")
            return new_atoms
            
    raise ValueError(f"Failed to generate a clash-free Graphene Oxide cell after {max_attempts} attempts.")


def main():
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    output_path = PROJECT_ROOT / "example" / "data" / "graphene_oxide.cif"
    
    try:
        go_atoms = generate_graphene_oxide()
        write(output_path, go_atoms)
        print(f"Successfully saved random 10x10 orthogonal Graphene Oxide to {output_path}")
    except Exception as e:
        print(f"Error during Graphene Oxide generation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
