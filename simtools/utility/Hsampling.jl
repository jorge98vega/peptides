#!/bin/sh
#=
exec julia -O3 "$0" -- $@
=#


include("Hsampling.in")


function main()
    # Initialize
    
    
    # Write the restraints file
    open(rstfile, "w") do file
    
        if length(WATs) > 0
            println(file, "#####################################")
	    println(file, "####            WATs             ####")
	    println(file, "#####################################")
            for atom in WATs # Loop over each oxygen
	        for hyd in 1:2 # Loop over each hydrogen
		    println(file, "&rst iresid = 0,")
		    println(file, "     iat = ", atom+1, ", ", atom+1+hyd, ",")
		    println(file, "     ifvari = 0,")
		    println(file, "     r1 = 0, r2 = 0.0, r3 = 5.0, r4 = 9999,")
		    println(file, "     rk2 = 0, rk3 = 0,")
		    println(file, "&end")
		    println(file, "#####################################")
		end
	    end
        end
	
	if length(NZs_LYN) > 0
            println(file, "#####################################")
	    println(file, "####           NZs_LYN           ####")
	    println(file, "#####################################")
            for atom in NZs_LYN # Loop over each nitrogen
	        for hyd in 1:2 # Loop over each hydrogen
		    println(file, "&rst iresid = 0,")
		    println(file, "     iat = ", atom+1, ", ", atom+1+hyd, ",")
		    println(file, "     ifvari = 0,")
		    println(file, "     r1 = 0, r2 = 0.0, r3 = 5.0, r4 = 9999,")
		    println(file, "     rk2 = 0, rk3 = 0,")
		    println(file, "&end")
		    println(file, "#####################################")
		end
	    end
        end
	
	if length(NZs_LYS) > 0
            println(file, "#####################################")
	    println(file, "####           NZs_LYS           ####")
	    println(file, "#####################################")
            for atom in NZs_LYS # Loop over each nitrogen
	        for hyd in 1:3 # Loop over each hydrogen
		    println(file, "&rst iresid = 0,")
		    println(file, "     iat = ", atom+1, ", ", atom+1+hyd, ",")
		    println(file, "     ifvari = 0,")
		    println(file, "     r1 = 0, r2 = 0.0, r3 = 5.0, r4 = 9999,")
		    println(file, "     rk2 = 0, rk3 = 0,")
		    println(file, "&end")
		    println(file, "#####################################")
		end
	    end
        end
	
    end
end


main()
