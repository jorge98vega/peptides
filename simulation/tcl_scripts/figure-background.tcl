# VMD Visualization Script
# -------------------------
# This script is used to visualize molecular dynamics simulations with VMD.
# It sets up representations, colors, and materials for better visualization.
# Usage: 
#   vmd -e figure-background.tcl -args 'molecule_selection' parm7_file trajectory_files...
# Customize representations as needed.

# Define visualization materials
set materialfore AOEdgy  ;# Foreground material
set materialback AOChalky ;# Background material

# Get user-defined molecular selection from arguments
set selectionbonded [lindex $argv 0]

# Set up display settings
axes location off
display rendermode GLSL
display projection orthographic
display depthcue off
color Display Background white

# Load topology file
set parmfile [lindex $argv 1]
mol new $parmfile type parm7
mol delrep 0 top  ;# Remove default representation

# Define molecular representations
# 1. Dynamic Bonds - highlights interactions and structure
mol representation DynamicBonds 1.6 0.2 50.0
mol color Name
mol selection $selectionbonded and (not name H C N O or not protein)
mol material $materialfore
mol addrep top

# 2. Van der Waals (VDW) representation for atomic surfaces
mol representation VDW 0.2 50.0
mol color Name
mol selection $selectionbonded and (not name H C N O or not protein)
mol material $materialfore
mol addrep top

# 3. Hydrogen Bonds - highlights hydrogen-bond interactions
mol representation HBonds 3.2 16.0 8.0
mol color Name
mol selection $selectionbonded and name NZ HZ1 HZ2 HZ3 O H1 H2 OD1 OD2 OH HH
mol material $materialfore
mol addrep top

# 4. Licorice representation for backbone and hydrogen atoms
mol representation Licorice 0.2 50.0
mol color Name
mol selection (backbone or name H)
mol material $materialback
mol addrep top

# 5. Licorice representation for protein structure
mol representation Licorice 0.1 50.0
mol color Name
mol selection protein
mol material $materialback
mol addrep top

# Customize element colors
color Name C gray
color Name F green
color Name H silver

# Adjust RGB values for specific colors
color change rgb gray 0.450 0.450 0.450
color change rgb silver 0.900 0.900 0.900

# Modify material properties
material change Outline $materialfore 1.7
material change Ambient $materialback 0.65
material change Diffuse $materialback 0.35

# Load trajectory files from command-line arguments
foreach trajfile [lrange $argv 2 $argc-1] {
    mol addfile $trajfile type netcdf waitfor all
}
