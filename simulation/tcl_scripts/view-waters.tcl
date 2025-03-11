# VMD Visualization Script for Water Molecules in a Channel
# ---------------------------------------------------------
# This script highlights water molecules inside a channel over a specified range of frames.
# It reads a list of selected water molecules from an input file and assigns a "user" field for visualization.
#
# Usage:
#   vmd -e view-waters.tcl -args iWATs_canal.dat 4990 5000
#   - iWATs_canal.dat: File containing water molecules inside the channel per frame
#   - 4990: First frame to process
#   - 5000: Last frame to process (not included)
#
# Note:
# - Frames in VMD start from 0.
# - Customize representations as needed.
#
# Reference: http://www.theochem.ruhr-uni-bochum.de/~legacy.akohlmey/cpmd-vmd/part4.html

# Set display options
display projection orthographic
set material Opaque

# Get the total number of frames
set n [molinfo 0 get numframes]

# Create atom selections
set all [atomselect 0 {all}]
set Owats [atomselect 0 {water and name O}]

# Read frame range from command-line arguments
set first [lindex $argv 1]
set last [lindex $argv 2]

# Read the water molecules inside the channel from the input file
set f [open [lindex $argv 0]]
for {set i $first} {$i < $last} {incr i} {
    set atomsinsel($i) [gets $f]
}
close $f

# Initialize the "user" field for all frames outside the selected range
for {set i 0} {$i < $first} {incr i} {
    $all frame $i
    $all set user 0
}
for {set i $last} {$i < $n} {incr i} {
    $all frame $i
    $all set user 0
}

# Assign "user" field for the selected frames based on the input file
for {set i $first} {$i < $last} {incr i} {
    set insel {}
    $all frame $i
    $all set user 0
    foreach atom [$Owats get index] {
        # Check if the atom is in the selection list
        if {[lsearch -exact [split $atomsinsel($i) " "] $atom] >= 0} {
            lappend insel 1
        } else {
            lappend insel 0
        }
    }
    $Owats frame $i
    $Owats set user $insel
    unset insel
}

# Clean up selections
$Owats delete
$all delete
unset Owats all atomsinsel i n atom first last

# Define molecular representations
mol delrep 0 top  ;# Remove default representation

# 1. Lines representation for backbone
mol representation Lines 2.0
mol color Name
mol selection "backbone"
mol material $material
mol addrep top

# 2. Lines representation for the protein
mol representation Lines 2.0
mol color Name
mol selection "protein"
mol material $material
mol addrep top

# 3. Lines representation for water molecules inside the channel
mol representation Lines 2.0
mol color Name
mol selection {same residue as user > 0}
mol material $material
mol addrep top
mol selupdate 2 0 on  ;# Ensure representation updates dynamically
