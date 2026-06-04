#!/bin/sh
#=
exec julia -O3 "$0" -- $@
=#


include("restrainer.in")
Ntotal = Nrings*Natoms # Number of atoms in a nanotube
Nacs = Nrings*Nres # Number of alpha carbons in a nanotube


function main()
    # Initialize
    acs = zeros(Int64, Nacs) # Array with the alpha carbon indices
    
    # Read pdb information
    open(pdbfile) do file
        i = 1
        for line in eachline(file)
	    m = match(r"\h(\d+)\h+CA\h", line)
	    if !isnothing(m)
		acs[i] = parse(Int64, m.captures[1])
		i += 1
		i > Nacs && break
	    end
	end
    end
    
    # Write the restraints file
    open(rstfile, "w") do file
        
        println(file, "#### Restraints parameters used: ####")
	println(file, "# rings = ", rings)
	println(file, "# tubes = ", tubes)
	println(file, "# tips = ", tips)
	println(file, "# torsion = ", torsion)
	println(file, "# connect1 = ", connect1)
	println(file, "# connect2 = ", connect2)
	println(file, "# ifvari = ", ifvari)
	println(file, "# nstep1 = ", nstep1)
	println(file, "# nstep2 = ", nstep2)
	println(file, "# r3 = ", r3)
	println(file, "# r3a = ", r3a)
	println(file, "# rk3 = ", rk3)
	println(file, "# rk3a = ", rk3a)
	
        if rings
            println(file, "#####################################")
	    println(file, "####            Rings            ####")
	    println(file, "#####################################")
            for tube in 0:Ntubes-1 # Loop over each nanotube
	        for ring in 1:Nrings-1 # Loop over each ring-ring restraint
		    println(file, "&rst iresid = 0,")
		    println(file, "     iat = -1, -1,")
		    print(file, "     igr1 = ")
	            for res in 1:Nres
		        print(file, acs[Nres*(ring-1)+res] + tube*Ntotal, ",")
		    end
		    print(file, "\n     igr2 = ")
		    for res in 1:Nres
		        print(file, acs[Nres*ring+res] + tube*Ntotal, ",")
		    end
		    println(file, "\n     ifvari = 0,")
		    println(file, "     r1 = 0, r2 = 0.0, r3 = 5.0, r4 = 9999,")
		    println(file, "     rk2 = ", rk3, ", rk3 = ", rk3, ",")
		    println(file, "&end")
		    println(file, "#####################################")
		end
	    end
        end

	if tubes
	    println(file, "#####################################")
	    println(file, "####            Tubes            ####")
	    println(file, "#####################################")
	    for index in 1:length(connect1)
	        println(file, "&rst iresid = 0,")
		println(file, "     iat = -1, -1,")
		print(file, "     igr1 = ")
		for ring in 0:Nrings-1
		    for res in 1:Nres
		        print(file, acs[Nres*ring+res] + connect1[index]*Ntotal, ",")
		    end
		end
		print(file, "\n     igr2 = ")
		for ring in 0:Nrings-1
		    for res in 1:Nres
		        print(file, acs[Nres*ring+res] + connect2[index]*Ntotal, ",")
		    end
		end
		print(file, "\n     ifvari = ", convert(Int64, ifvari), ",")
		ifvari && print(file, " nstep1 = ", nstep1, ", nstep2 = ", nstep2, ",")
		println(file, "\n     r1 = 0, r2 = 0.0, r3 = ", r3, ", r4 = 9999,")
		ifvari && println(file, "     r1a = 0, r2a = 0.0, r3a = ", r3a, ", r4a = 9999,")
		println(file, "     rk2 = ", rk3, ", rk3 = ", rk3, ",")
		ifvari && println(file, "     rk2a = ", rk3a, ", rk3a = ", rk3a, ",")
	        println(file, "&end")
	        println(file, "#####################################")
	    end
	end

	if tips
	    println(file, "#####################################")
	    println(file, "####            Tips             ####")
	    println(file, "#####################################")
	    for index in 1:length(connect1)
	        for ring in [0, Nrings-1]
	            println(file, "&rst iresid = 0,")
		    println(file, "     iat = -1, -1,")
		    print(file, "     igr1 = ")
	            for res in 1:Nres
		        print(file, acs[Nres*ring+res] + connect1[index]*Ntotal, ",")
		    end
		    print(file, "\n     igr2 = ")
		    for res in 1:Nres
		        print(file, acs[Nres*ring+res] + connect2[index]*Ntotal, ",")
		    end
		    print(file, "\n     ifvari = ", convert(Int64, ifvari), ",")
		    ifvari && print(file, " nstep1 = ", nstep1, ", nstep2 = ", nstep2, ",")
		    println(file, "\n     r1 = 0, r2 = 0.0, r3 = ", r3, ", r4 = 9999,")
		    ifvari && println(file, "     r1a = 0, r2a = 0.0, r3a = ", r3a, ", r4a = 9999,")
		    println(file, "     rk2 = ", rk3, ", rk3 = ", rk3, ",")
		    ifvari && println(file, "     rk2a = ", rk3a, ", rk3a = ", rk3a, ",")
		    println(file, "&end")
		    println(file, "#####################################")
		end
	    end
	end

	if torsion
	    println(file, "#####################################")
	    println(file, "####           Torsion           ####")
	    println(file, "#####################################")
	    for index in 1:length(connect1)
	        println(file, "&rst iresid = 0,")
		print(file, "     iat = ")
		print(file, acs[1] + connect1[index]*Ntotal, ",")
		print(file, acs[1] + connect2[index]*Ntotal, ",")
		print(file, acs[Nres*(Nrings-1)+1] + connect2[index]*Ntotal, ",")
		println(file, acs[Nres*(Nrings-1)+1] + connect1[index]*Ntotal, ",")
		println(file, "     ifvari = 0,")
		println(file, "     r1 = -180, r2 = -5, r3 = 5, r4 = 180,")
		println(file, "     rk2 = ", rk3, ", rk3 = ", rk3, ",")
		println(file, "&end")
		println(file, "#####################################")
	    end
	end
    end
end


main()
