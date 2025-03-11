# VMD Visualization Script for QM/MM Regions
# ------------------------------------------
# This script is used to visualize QM/MM regions in molecular dynamics simulations.
# It automatically loads the QM region from 'qmmask.dat' and applies various representations.
# Usage: 
#   vmd -e view-qmmm.tcl
# Customize representations as needed.

# Define material for all representations
set material Opaque

# Load QM region selection from 'qmmask.dat'
set fm1 [open qmmask.dat]
set m1 "[read $fm1]"
close $fm1
set m1nh "$m1 and not hydrogen"  ;# Exclude hydrogen atoms for better visualization

# Set display options
display projection orthographic

# Remove default representation
mol delrep 0 top

# 1. Dynamic Bonds for non-hydrogen QM region
mol representation DynamicBonds 1.7 0.2 12.0
mol color Name
mol selection $m1nh
mol material $material
mol addrep top

# 2. Dynamic Bonds for full QM region
mol representation DynamicBonds 1.3 0.2 12.0
mol color Name
mol selection $m1
mol material $material
mol addrep top

# 3. Lines representation for the QM region
mol representation Lines 2.0
mol color Name
mol selection $m1
mol material $material
mol addrep top

# 4. Van der Waals (VDW) representation for QM region
mol representation VDW 0.2 12.0
mol color Name
mol selection $m1
mol material $material
mol addrep top

# 5. Licorice representation for backbone structure
mol representation Licorice 0.15
mol color Name
mol selection "backbone"
mol material $material
mol addrep top

# 6. Lines representation for water molecules
mol representation Lines 0.15
mol color Name
mol selection "water"
mol material $material
mol addrep top

# 7. Lines representation for TFA (Trifluoroacetic Acid) molecules
mol representation Lines 0.15
mol color Name
mol selection "resname TFA"
mol material $material
mol addrep top
