import numpy as np
import random as rnd
from hybrid_36 import hy36encode,hy36decode

class Nucl_Data:
    def __init__(self) -> None:
        self.pdbfile = ""
        self.xyz, self.res, self.atn, self.ter = [],[],[],[]
        self.lines = []
        self.pur_atom = ("N1","C2","H2-N2","N3","C4","C5","C6","O6-N6","N7","C8","N9","COM")
        self.pyr_atom = ("N1","C2","O2","N3","C4","O4-N4","C5","C6","H7-C7","COM")
        self.sug_atom = ("C1'","C2'","C3'","C4'","C5'","H2'-O2'","O3'","O4'","O5'","COM")
        self.phos_atom = ("P","OP1","O1P","OP2","O2P","O5'","COM")
        self.P, self.S, self.B = [],[],[]

class Prot_Data:
    def __init__(self) -> None:
        self.amino_acid_dict = {'CYS': 'C', 'ASP': 'D', 'SER': 'S', 'GLN': 'Q', 'LYS': 'K',
            'ILE': 'I', 'PRO': 'P', 'THR': 'T', 'PHE': 'F', 'ASN': 'N',
            'GLY': 'G', 'HIS': 'H', 'LEU': 'L', 'ARG': 'R', 'TRP': 'W',
            'ALA': 'A', 'VAL': 'V', 'GLU': 'E', 'TYR': 'Y', 'MET': 'M'}
        self.pdbfile = ""
        self.xyz, self.res, self.atn, self.ter = [],[],[],[]
        self.lines = []
        self.CA, self.CB = [],[]

class CoarseGrain:
    def __init__(self) -> None:
        self.mass = {"H":1.008,"C":12.011,"N":14.007,"O":15.999,"S":32.065,"P":30.974}    
    
    def get_BB_group(self,reslist,atnum):
        assert len(reslist) == len(atnum)
        return [reslist[x] for x in range(len(reslist))]

    def get_SC_group(self,reslist,atnum):
        assert len(reslist) == len(atnum)
        bb_group,sc_group = dict(),dict()
        for x in range(len(reslist)):
            chain,resnum,resname,atname = reslist[x]
            if resname in Prot_Data().amino_acid_dict:
                if (chain,resnum,resname) not in bb_group:
                    bb_group[(chain,resnum,resname)] = []
                    sc_group[(chain,resnum,resname)] = []
                if atname in ["N","CA","C","O","H","OXT"]: bb_group[(chain,resnum,resname)].append(atnum[x])
                else: sc_group[(chain,resnum,resname)].append(atnum[x])
            elif resname[-1] in "AUTGC": 
                assert len(resname) < 3
                continue
        return bb_group,sc_group

    def get_CA_COM(self,reslist,XYZ):
        #calculate COM of the bakcbone#
        assert len(reslist) == len(XYZ)
        bb_xyz,bb_mass = dict(),dict()
        for x in range(XYZ.shape[0]):
            chain,resnum,resname,atname = reslist[x]
            if (chain,resnum,resname) not in bb_xyz: bb_xyz[(chain,resnum,resname)],bb_mass[(chain,resnum,resname)] = [],[]
            if atname in ["N","CA","C","O","H","OXT"]:
                bb_xyz[(chain,resnum,resname)].append(XYZ[x])
                bb_mass[(chain,resnum,resname)].append(self.mass[atname[0]])
        COM = {}
        for resnum in bb_xyz:
            C,M=np.float_(bb_xyz[resnum]),np.float_(bb_mass[resnum])
            COM[resnum]=np.matmul(M,C)/sum(M)
        return COM

    def get_CA_atom(self,reslist,XYZ):
        assert len(reslist) == len(XYZ)
        CA = {}
        for x in range(XYZ.shape[0]):
            chain,resnum,resname,atname = reslist[x]
            if atname == "CA": CA[(chain,resnum,resname)]=XYZ[x]
        return CA

    def get_CB_COM(self,reslist,XYZ,inc_gly):
        #calculate COM of the bakcbone#
        assert len(reslist) == len(XYZ)
        sc_xyz,sc_mass = dict(),dict()
        CB_for_H = 0
        gly_count = 0
        for x in range(XYZ.shape[0]):
            chain,resnum,resname,atname = reslist[x]
            if (chain,resnum,resname) not in sc_xyz: sc_xyz[(chain,resnum,resname)],sc_mass[(chain,resnum,resname)] = [],[]
            if resname == "GLY" and atname == "CA": gly_count += 1
            if atname not in ["N","CA","C","O","H","OXT"]:
                sc_xyz[(chain,resnum,resname)].append(XYZ[x])
                sc_mass[(chain,resnum,resname)].append(self.mass[atname[0]])
                if resname == "GLY" and inc_gly: CB_for_H += 1
        if inc_gly: assert CB_for_H == 2*gly_count, "Error. GLY found without H-atom. Cannot use CB_gly. Add H-atom to the PDB"
    
        COM = {}
        for resnum in sc_xyz:
            C,M=np.float_(sc_xyz[resnum]),np.float_(sc_mass[resnum])
            COM[resnum]=np.matmul(M,C)/sum(M)
        return COM

    def get_CB_atom(self,reslist,XYZ,inc_gly):
        assert len(reslist) == len(XYZ)
        CB = {}
        CB_for_H = 0
        gly_count = 0
        for x in range(XYZ.shape[0]):
            chain,resnum,resname,atname = reslist[x]
            if atname == "CB": CB[(chain,resnum,resname)]=XYZ[x]
            if resname == "GLY":
                if atname == "CA": gly_count += 1
                if inc_gly:
                    if atname=="CB" or atname == "HA3":
                        CB[(chain,resnum,resname)]=XYZ[x]
                        CB_for_H += 1
        if inc_gly: assert CB_for_H == gly_count, "Error. GLY found without H-atom. Cannot use CB_gly. Add H-atom to the PDB"
        else: assert CB_for_H == 0
        return CB

    def get_CB_far(self,reslist,XYZ,inc_gly):
        assert len(reslist) == len(XYZ)
        CA,sc_xyz = {},{}
        CB_for_H = 0
        gly_count = 0
        for x in range(XYZ.shape[0]):
            chain,resnum,resname,atname = reslist[x]
            if atname == "CA": 
                CA[(chain,resnum,resname)]=XYZ[x]
                if resname == "GLY": gly_count += 1
            if (chain,resnum,resname) not in sc_xyz: sc_xyz[(chain,resnum,resname)]=[]
            if atname not in ["N","CA","C","O","H","OXT"]:
                sc_xyz[(chain,resnum,resname)].append(XYZ[x])
                if resname == "GLY" and inc_gly: CB_for_H += 1
        if inc_gly: assert CB_for_H == 2*gly_count, "Error. GLY found without H-atom. Cannot use CB_gly. Add H-atom to the PDB"

        CB = {}
        for resnum in CA:
            sc_xyz[resnum]=np.float_(sc_xyz[resnum])
            if sc_xyz[resnum].shape[0]==0:continue
            sq_dist = np.sum((CA[resnum]-sc_xyz[resnum])**2,1)
            CB[resnum]=sc_xyz[resnum][np.where(sq_dist==np.max(sq_dist))[0][0]]
        return CB

    def get_P_beads(self, reslist,XYZ,position):
        position = position.upper()
        assert len(reslist) == len(XYZ)
        bb_xyz,bb_mass = dict(),dict()
        if position == "COM":
            prev_O3prime = []
            for x in range(XYZ.shape[0]):
                chain,resnum,resname,atname = reslist[x]
                if (chain,resnum,resname) not in bb_xyz: bb_xyz[(chain,resnum,resname)],bb_mass[(chain,resnum,resname)] = [],[]
                if "P" in atname or atname=="O5'":
                    bb_xyz[(chain,resnum,resname)].append(XYZ[x])
                    bb_mass[(chain,resnum,resname)].append(self.mass[atname[0]])
                    if atname == "O5'" and len(prev_O3prime) != 0:
                        if chain==prev_O3prime[0][0]:
                            bb_xyz[(chain,resnum,resname)].append(prev_O3prime[1])
                            bb_mass[(chain,resnum,resname)].append(self.mass[prev_O3prime[0][-1][0]])
                if atname == "O3'": prev_O3prime = [reslist[x],XYZ[x]]
            COM = {}
            for resnum in bb_xyz:
                C,M=np.float_(bb_xyz[resnum]),np.float_(bb_mass[resnum])
                COM[resnum]=np.matmul(M,C)/sum(M)
            return COM
        else:
            assert "P" in position or atname=="O5'"
            P = {}
            for x in range(XYZ.shape[0]):
                chain,resnum,resname,atname = reslist[x]
                if atname == position: P[(chain,resnum,resname)]=XYZ[x]
            return P

    def get_S_beads(self, reslist,XYZ,position):
        position = position.upper()
        assert len(reslist) == len(XYZ)
        bb_xyz,bb_mass = dict(),dict()
        if position == "COM":
            for x in range(XYZ.shape[0]):
                chain,resnum,resname,atname = reslist[x]
                if (chain,resnum,resname) not in bb_xyz: bb_xyz[(chain,resnum,resname)],bb_mass[(chain,resnum,resname)] = [],[]
                if "'" in atname:
                    bb_xyz[(chain,resnum,resname)].append(XYZ[x])
                    bb_mass[(chain,resnum,resname)].append(self.mass[atname[0]])
            COM = {}
            for resnum in bb_xyz:
                C,M=np.float_(bb_xyz[resnum]),np.float_(bb_mass[resnum])
                COM[resnum]=np.matmul(M,C)/sum(M)
            return COM
        else:
            assert "'" in position
            S = {}
            for x in range(XYZ.shape[0]):
                chain,resnum,resname,atname = reslist[x]
                if atname == position: S[(chain,resnum,resname)]=XYZ[x]
            return S

    def get_B_beads(self, reslist,XYZ,position,Btype):
        position = [x.upper() for x in position]
        assert len(reslist) == len(XYZ)
        bb_xyz,bb_mass = dict(),dict()
        if "COM" in position: 
            assert len(position) == 1
            for x in range(XYZ.shape[0]):
                chain,resnum,resname,atname = reslist[x]
                if resname[-1] in Btype:
                    if (chain,resnum,resname) not in bb_xyz: bb_xyz[(chain,resnum,resname)],bb_mass[(chain,resnum,resname)] = [],[]
                    if "P" not in atname and  "'" not in atname:
                        bb_xyz[(chain,resnum,resname)].append(XYZ[x])
                        bb_mass[(chain,resnum,resname)].append(self.mass[atname[0]])
            COM = {}
            for resnum in bb_xyz:
                C,M=np.float_(bb_xyz[resnum]),np.float_(bb_mass[resnum])
                COM[resnum] = [np.matmul(M,C)/sum(M)]
            return COM
        else:
            assert "'" not in position and "P" not in position
            B = {}
            for x in range(XYZ.shape[0]):
                chain,resnum,resname,atname = reslist[x]
                if resname[-1] in Btype:
                    if atname in position: 
                        if (chain,resnum,resname) not in B: B[(chain,resnum,resname)] = []
                        B[chain,resnum,resname].append(XYZ[x])
            return B

class PDB_IO:
        
    def __init__(self,fileindex=0,nfiles=1) -> None:
        self.file_ndx=[str(fileindex),str()][int(nfiles==1)]
        self.nucleotide_dict = nucl_res = {x:x[-1] for x in ("A","G","T","U","C","DA","DG","DT","DC")}
        self.nucl = Nucl_Data()
        self.prot = Prot_Data()
        self.nucl.pdbfile = ""
        self.prot.pdbfile = ""
        self.refined_pdbfile = ""
        self.pdbfile = '"'
        self.nucl.xyz, self.nucl.res, self.nucl.atn, self.nucl.ter, self.nucl.cid, self.nucl.deoxy = [],[],[],[],[],[]
        self.prot.xyz, self.prot.res, self.prot.atn, self.prot.ter, self.prot.cid = [],[],[],[],[]
        self.nucl.lines,self.prot.lines = [],[]
        self.original_chain_order = []
        self.nucl.seq, self.prot.seq = str(),str()
        return
       
    def __readPDB__(self):
        #reading all atom pdb data
        if len(self.nucl.lines) > 0:
            nucl_chain_count = 0
            bbseq = str()
            for x in range(len(self.nucl.lines)):
                l=self.nucl.lines[x]
                if l.startswith("ATOM"):
                    self.nucl.xyz.append([l[30:38],l[38:46],l[46:54]])
                    self.nucl.res.append((nucl_chain_count,hy36decode(4,l[22:26]),l[17:20].strip(),l[12:16].strip()))
                    self.nucl.atn.append(-1+hy36decode(5,l[6:11]))
                    if l[12:16].strip() in (("C0'","C1'","C'")): self.nucl.seq += l[17:20].strip()[-1]
                    if l[12:16].strip() == "P": bbseq += l[17:20].strip()[-1]
                if l.startswith(("TER","END")) and self.nucl.lines[x-1].startswith("ATOM"):
                    self.nucl.ter.append(hy36decode(5,self.nucl.lines[x-1][6:11]))
                    self.nucl.cid.append(self.nucl.lines[x-1][21])
                    self.nucl.deoxy.append(self.nucl.lines[x-1][17:20].strip()[0]=="D")
                    nucl_chain_count+=1
                    self.nucl.seq += " "
            if len(self.nucl.seq) == 0: self.nucl.seq = bbseq
            else: assert len(self.nucl.seq) >= len(bbseq), "Error missing sugar atoms"
            self.nucl.xyz=np.float_(self.nucl.xyz); self.nucl.atn=np.int_(self.nucl.atn); self.nucl.ter=np.int_(self.nucl.ter)
        if len(self.prot.lines) > 0:
            prot_chain_count = 0
            for x in range(len(self.prot.lines)):
                l=self.prot.lines[x]
                if l.startswith("ATOM"):
                    self.prot.xyz.append([l[30:38],l[38:46],l[46:54]])
                    self.prot.res.append((prot_chain_count,hy36decode(4,l[22:26]),l[17:20].strip(),l[12:16].strip()))
                    self.prot.atn.append(-1+hy36decode(5,l[6:11]))
                    if l[12:16].strip() == "CA": self.prot.seq += self.prot.amino_acid_dict[l[17:20]]
                if l.startswith(("TER","END")) and self.prot.lines[x-1].startswith("ATOM"):
                    self.prot.ter.append(hy36decode(5,self.prot.lines[x-1][6:11]))
                    self.prot.cid.append(self.prot.lines[x-1][21])
                    prot_chain_count+=1
                    self.prot.seq += " "
            self.prot.xyz=np.float_(self.prot.xyz); self.prot.atn=np.int_(self.prot.atn); self.prot.ter=np.int_(self.prot.ter)
        return
    
    def __fixNultiOcc__(self,pdb_lines=list()):
        multi_occ = dict()  #pdb lines hashed to atom name
        fixed_lines = list()
        for line in pdb_lines:
            if line.startswith(("ATOM","HETATM")) and line[16] != " ": #Multiple occ
                resnum = int(line[22:26])
                atname = line[12:16].strip()
                if resnum not in multi_occ: multi_occ[resnum] = dict()
                if atname not in multi_occ[resnum]: multi_occ[resnum][atname] = list()  
                multi_occ[resnum][atname].append((float(line[54:60]),line))
            elif line.startswith(("TER","END")) or line[16] == " ": # no multiple occ
                if len(multi_occ) != 0:
                    for resnum in multi_occ:
                        for atnmae in multi_occ[resnum]:
                            multi_occ[resnum][atnmae].sort()    #sorting
                            #loadig the one with maximum occ
                            prev_line = multi_occ[resnum][atnmae][-1][1]
                            fixed_lines.append(prev_line)
                    multi_occ = dict()
                fixed_lines.append(line)
        return fixed_lines

    def __readLnes__(self,infile):
        nucl_lines = list(); prot_lines = list()
        with open(infile) as fin:
            prev_resname,prev_resnum = str(),0
            for line in fin:
                if line.startswith(("ATOM","HETATM")):
                    atname=line[12:16].strip()
                    if atname.startswith("H") and not self.CBgly: continue
                    resname,resnum =  line[17:20].strip(),hy36decode(4,line[22:26])
                    if prev_resnum not in (resnum,resnum-1) and len(prev_resname)!=0:
                        if prev_resname in self.prot.amino_acid_dict: prot_lines.append("TER\n")
                        elif prev_resname in self.nucleotide_dict: nucl_lines.append("TER\n")
                    if resname in self.prot.amino_acid_dict: prot_lines.append("ATOM".ljust(6)+line[6:])
                    elif resname in self.nucleotide_dict: nucl_lines.append("ATOM".ljust(6)+line[6:])
                    prev_resname,prev_resnum = resname,resnum
                if line.startswith(("TER","END")):
                    if resname in self.prot.amino_acid_dict:
                        if prot_lines[-1].startswith("TER"): continue
                        self.original_chain_order.append(('prot',prot_lines[-1][21]))
                        prot_lines.append(line)
                    elif resname in self.nucleotide_dict:
                        if nucl_lines[-1].startswith("TER"): continue
                        self.original_chain_order.append(('nucl',nucl_lines[-1][21]))
                        nucl_lines.append(line)
                    prev_resname,prev_resnum = str(),0
            if len(nucl_lines) != 0:
                nucl_lines = self.__fixNultiOcc__(pdb_lines=nucl_lines)
                if not nucl_lines[-1].startswith(("TER","END")):
                    self.original_chain_order.append(('nucl',nucl_lines[-1][21]))
                    nucl_lines.append("TER\n")
            if len(prot_lines) != 0:
                prot_lines = self.__fixNultiOcc__(pdb_lines=prot_lines)           
                if not prot_lines[-1].startswith(("TER","END")):
                    self.original_chain_order.append(('prot',prot_lines[-1][21]))
                    prot_lines.append("TER\n")
        self.nucl.lines = nucl_lines
        self.prot.lines = prot_lines
        return infile

    def __refinePDB__(self,infile):
        print (">>> Renumbering atoms. \n>>> The chain_id and residue number remains same,", infile)
        chain_terminal = list()

        self.__readLnes__(infile=infile)
        outfile = ".".join(infile.split(".")[:-1]+["refined"])
        self.refined_pdbfile = outfile+".pdb"
        fout = open(self.refined_pdbfile,"w+")
        atcount,last_count = 0,0
        nucl_lines,prot_lines = [],[]
        if len(self.nucl.lines) != 0:
            print (">> Found nucleic-acid molecule(s)")
            self.nucl.pdbfile = outfile+".nucl.pdb"
            with open(self.nucl.pdbfile,"w+") as fnuc:
                for line in self.nucl.lines:
                    if line.startswith("ATOM"):
                        atcount += 1
                        line = line[:6]+hy36encode(5,atcount)+line[11:]
                    fout.write(line)
                    fnuc.write(line)
                    nucl_lines.append(line)
            last_count = atcount
            assert len(self.nucl.lines) == len(nucl_lines)
            self.nucl.lines = nucl_lines
        if len(self.prot.lines)!=0:
            print (">> Found protein molecule(s)")
            atcount = 0
            self.prot.pdbfile = outfile+".prot.pdb"
            with open(self.prot.pdbfile,"w+") as fpro:
                for line in self.prot.lines:
                    if line.startswith("ATOM"):
                        atcount += 1
                        line = line[:6]+hy36encode(5,atcount)+line[11:]
                    fout.write(line)
                    fpro.write(line)
                    prot_lines.append(line)
            assert len(self.prot.lines) == len(prot_lines)
            self.prot.lines = prot_lines
        return outfile+".pdb"

    def loadfile(self, infile, refine=True, CBgly=False):
        self.CBgly=CBgly
        if refine: self.pdbfile=self.__refinePDB__(infile=infile)
        else: self.pdbfile=self.__readLnes__(infile=infile)
        self.__readPDB__()
        return infile

    def __call__(self, infile, refine=True):
        self.loadfile(infile=infile,refine=refine)

    def coordinateTransform(self):
        #when a custom nucleic acid structure is added to the pdb,
        #the co-ordintaes of the RNA/DNA may overlap with those of protein.
        #This function moves the geometric center of the the DNA/RNA at a distance
        #equal to sum of radius of protein and DNA/RNA macromolecule
        #Radius is defined here as the distance of the farthest atom from the geometric center
        #Although the distance is same, the position is randomly determined
        #this function is called if custom_nuc input is true
        #and returns name of the new aligned nuc pdb file
        
        #protein coordinates
        coord = self.prot.xyz
        #geometric center of aa structure
        prot_geocent = np.sum(coord,0)/len(coord)
        coord = coord-prot_geocent

        #maximum distance of any atom from geometric center (0,0,0)
        #this ditacnce will define the radius of a sphere that can completely surround the protein
        prot_rad = np.max(np.sum(coord**2,1)**0.5)
        print ("Protein Geometric center = ",prot_geocent," approximate radius = ",prot_rad)

        #nucleotide coordinates
        coord = self.nucl.xyz

        #geometric center of aa structure
        #calculated by averaging over all coordinates
        nucl_geocent = np.sum(coord,0)/len(coord);
        coord = coord-nucl_geocent
        nucl_rad = np.max(np.sum(coord**2,1)**0.5)
        print ("DNA/RNA Geometric center = ",nucl_geocent," approximate radius = ",nucl_rad)

        #minimum distance to be kept between protein and DNA/RNA centers
        dist = prot_rad+nucl_rad

        #for diagonal distances a*(3)^0.5 = dist, hence a = dist/3**0.5
        #a = dist/3**0.5    #equal tranformation in all three co-ordinates
        #let alpha be the angle of trans_vec (transformation verctor) with Z.axis
        #let beta be the angle of the XY projection of trans_vec with X aixis

        #Randomly genrating tranformation vector with minimu dist as determined above
        trans_vec = dist*rnd.uniform(1,1.5) #The actual value of dist will be randomly increased by 1-> 1.5 times
        alpha = rnd.uniform(0,2*np.pi)
        beta = rnd.uniform(0,2*np.pi)
        X_trans = trans_vec*np.sin(alpha)*np.cos(beta)
        Y_trans = trans_vec*np.sin(alpha)*np.sin(beta)
        Z_trans = trans_vec*np.cos(alpha)

        #definfing new coordinates for nucleic acid structure
        new_nucl_geocent = prot_geocent + np.float_([X_trans,Y_trans,Z_trans])
        print ("DNA/RNA new Geometric center = ",new_nucl_geocent)

        #defining linear transition matrix for moving FNA/RNA
        trans_matrix = new_nucl_geocent - nucl_geocent

        #writing new co-ordinates to the file
        self.nucl.xyz = self.nucl.xyz + trans_matrix

        #output pdb file 
        outfile = ".".join(self.nucl.pdbfile.split(".")[:-1]+["trans.pdb"])
        self.nucl.pdbfile = outfile
        with open(outfile,"w+") as fout:
            count = 0
            for x in range(len(self.nucl.lines)):
                line = self.nucl.lines[x]
                if line.startswith("ATOM"):
                    self.nucl.xyz[count]
                    fout.write(line[:6]+hy36encode(5,1+self.nucl.atn[count])+line[11:30])
                    fout.write(3*"%8.3f"%tuple(self.nucl.xyz[count]))
                    fout.write(line[54:])
                    count += 1
                else:#TER and END
                    fout.write(line)

        #appaending atomnum number in prot.pdbfile
        #self.prot.atn += self.nucl.atn[-1]
        outfile = ".".join(self.prot.pdbfile.split(".")[:-1]+["trans.pdb"])
        self.prot.pdbfile = outfile
        with open(outfile,"w+") as fout:
            count = 0
            for line in self.prot.lines:
                if line.startswith("ATOM"):
                    fout.write(line[:6]+hy36encode(5,1+self.prot.atn[count])+line[11:])
                    count+=1
                else: fout.write(line)

        return

    def __combineGro__(self,outfile):
        with open(outfile,"w+") as fout:
            fout.write("CG file %s for GROMACS\n"%(outfile))
            fnucl,fprot = open("nucl_"+outfile),open("prot_"+outfile)
            nucl_natoms = int([fnucl.readline() for x in range(2)][-1])
            prot_natoms = int([fprot.readline() for x in range(2)][-1])
            fout.write("%d\n"%(nucl_natoms+prot_natoms))
            for x in range(nucl_natoms): fout.write(fnucl.readline())
            for x in range(prot_natoms):
                line = fprot.readline()
                line = line[:15]+hy36encode(5,nucl_natoms+int(line[15:20]))+line[20:]
                fout.write(line)
            fout.write(fnucl.readline())
            fnucl.close();fprot.close()
        return
            
    def cmapSplit(self,cmap):
        #if input cmap given, splitting protein and nucl sections
        return_files={"nucl":str(),"prot":str(),"inter":str()}
        if len(self.nucl.lines)>0: fnucl=open(cmap+".nuclcont","w+")
        if len(self.prot.lines)>0: fprot=open(cmap+".protcont","w+")
        if len(self.nucl.lines)>0 and len(self.prot.lines)>0:
            finter=open("inter.cont","a") #append
        with open(cmap) as fin:
            for line in fin:
                if line.startswith(("#","@",";")): continue
                line=line.split()
                c1,a1,c2,a2=line[:4]
                a1,a2=np.int_([a1,a2])-1
                if "p" in c1 or "n" in c1:
                    assert "p" in c2 or "n" in c2
                else:
                    n1,n2=np.int_([c1,c2])-1
                    c1="%s_%s"%(self.original_chain_order[n1][0],c1)
                    c2="%s_%s"%(self.original_chain_order[n2][0],c2)
                a1,a2=np.int_([a1,a2])+1
                if c1[0]==c2[0]=="n":
                    fnucl.write("%s %d %s %d"%(c1,a1,c2,a2))
                    fnucl.write(len(line[4:])*" %s"%tuple(line[4:])+"\n")
                elif c1[0]==c2[0]=="p":
                    fprot.write("%s %d %s %d"%(c1,a1,c2,a2))
                    fprot.write(len(line[4:])*" %s"%tuple(line[4:])+"\n")
                elif c1[0]!=c2[0]:
                    finter.write("%s %d %s %d"%(c1,a1,c2,a2))
                    finter.write(len(line[4:])*" %s"%tuple(line[4:])+"\n")
        if len(self.nucl.lines)>0: return_files["nucl"]=cmap+".nuclcont";fnucl.close()
        if len(self.prot.lines)>0: return_files["prot"]=cmap+".protcont";fprot.close()
        if len(self.prot.lines)>0 and len(self.nucl.lines)>0:
            return_files["inter"]="inter.cont";finter.close()
        return return_files

    def write_CG_protfile(self,CGlevel,CAcom,CBcom,CBfar,CBgly,nucl_pos,outgro):
        #writes coarse grain pdb and gro files

        det = CoarseGrain()
        
        if len(self.prot.lines) != 0:
            prot_grofile = "prot%s_%s"%(self.file_ndx,outgro)
            #default CA position: CA-atom
            if CAcom: self.prot.CA = det.get_CA_COM(reslist=self.prot.res,XYZ=self.prot.xyz)
            else: self.prot.CA = det.get_CA_atom(reslist=self.prot.res,XYZ=self.prot.xyz)
            self.prot.bb_file = ".".join(self.prot.pdbfile.split(".")[:-1]+["native_CA.pdb"])
            self.prot.CA_atn = dict()
            with open(self.prot.bb_file,"w+") as fout:
                atcount,prev_chain = 0,0
                fgro = open(prot_grofile,"w+")
                fgro.write("CG file %s for GROMACS\n%d\n"%(prot_grofile,len(self.prot.CA)))
                self.prot.group = []
                for res in self.prot.CA: 
                    self.prot.CA_atn[res] = atcount
                    atcount+=1
                    if res[0]!=prev_chain: fout.write("TER\n")
                    line = "ATOM".ljust(6)+hy36encode(5,atcount)+" "+"CA".center(4)+" "+res[-1].rjust(3)+" "+self.prot.cid[res[0]]+hy36encode(4,res[1])+4*" "+3*"%8.3f"%tuple(self.prot.CA[res])
                    fout.write(line+"\n")
                    line = str(res[1]).rjust(5)+res[-1].ljust(5)+"CA".center(5)+hy36encode(5,atcount).rjust(5)+3*"%8.3f"%tuple(0.1*self.prot.CA[res])
                    fgro.write(line+"\n")
                    
                    prev_chain = res[0]
                fout.write("END\n")
                fgro.write("%8.3f%8.3f%8.3f"%(0,0,0))
                fgro.close()

            if CGlevel["prot"] == 2:
                if CBcom: self.prot.CB = det.get_CB_COM(reslist=self.prot.res,XYZ=self.prot.xyz,inc_gly=CBgly)
                elif CBfar: self.prot.CB = det.get_CB_far(reslist=self.prot.res,XYZ=self.prot.xyz,inc_gly=CBgly)
                else: self.prot.CB = det.get_CB_atom(reslist=self.prot.res,XYZ=self.prot.xyz,inc_gly=CBgly)
                self.prot.sc_file = ".".join(self.prot.pdbfile.split(".")[:-1]+["native_CB.pdb"])
                self.prot.CB_atn = dict()
                with open(self.prot.sc_file,"w+") as fout:
                    fgro = open(prot_grofile,"w+")
                    fgro.write("CG file %s for GROMACS\n%d\n"%(prot_grofile,len(self.prot.CA)+len(self.prot.CB)))
                    atcount,prev_chain = 0,0
                    for res in self.prot.CA:
                        if res[0]!=prev_chain: fout.write("TER\n")
                        self.prot.CA_atn[res] = atcount
                        atcount+=1
                        line = "ATOM".ljust(6)+hy36encode(5,atcount)+" "+"CA".center(4)+" "+res[-1].rjust(3)+" "+self.prot.cid[res[0]]+hy36encode(4,res[1])+4*" "+3*"%8.3f"%tuple(self.prot.CA[res])
                        fout.write(line+"\n")
                        line = str(res[1]).rjust(5)+res[-1].ljust(5)+"CA".center(5)+hy36encode(5,atcount).rjust(5)+3*"%8.3f"%tuple(0.1*self.prot.CA[res])
                        fgro.write(line+"\n")
                        prev_chain = res[0]
                        if res not in self.prot.CB:
                            assert "GLY"  in res
                            continue
                        self.prot.CB_atn[res] = atcount
                        atcount+=1
                        line = "ATOM".ljust(6)+hy36encode(5,atcount)+" "+"CB".center(4)+" "+res[-1].rjust(3)+" "+self.prot.cid[res[0]]+hy36encode(4,res[1])+4*" "+3*"%8.3f"%tuple(self.prot.CB[res])
                        fout.write(line+"\n")
                        line = str(res[1]).rjust(5)+res[-1].ljust(5)+"CB".center(5)+hy36encode(5,atcount).rjust(5)+3*"%8.3f"%tuple(0.1*self.prot.CB[res])
                        fgro.write(line+"\n")
                        prev_chain = res[0]
                    fout.write("END\n")
                    fgro.write("%8.3f%8.3f%8.3f"%(0,0,0))
                    fgro.close()

        if len(self.nucl.lines) != 0:   
            nucl_grofile = "nucl%s_%s"%(self.file_ndx,outgro)
            self.nucl.P = det.get_P_beads(reslist=self.nucl.res,XYZ=self.nucl.xyz,position=nucl_pos["P"])
            self.nucl.bb_file = ".".join(self.nucl.pdbfile.split(".")[:-1]+["native_P.pdb"])
            self.nucl.P_atn = dict()
            with open(self.nucl.bb_file,"w+") as fout:
                atcount,prev_chain = 0,0
                fgro = open(nucl_grofile,"w+")
                fgro.write("CG file %s for GROMACS\n%d\n"%(nucl_grofile,len(self.nucl.P)))
                for res in self.nucl.P: 
                    self.nucl.P_atn[res] = atcount
                    atcount+=1
                    if res[0]!=prev_chain: fout.write("TER\n")
                    line = "ATOM".ljust(6)+hy36encode(5,atcount)+" "+"P".center(4)+" "+res[-1].rjust(3)+" "+self.nucl.cid[res[0]]+hy36encode(4,res[1])+4*" "+3*"%8.3f"%tuple(self.nucl.P[res])
                    fout.write(line+"\n")
                    line = str(res[1]).rjust(5)+res[-1].ljust(5)+"P".center(5)+hy36encode(5,atcount).rjust(5)+3*"%8.3f"%tuple(0.1*self.nucl.P[res])
                    fgro.write(line+"\n")
                    prev_chain = res[0]
                fout.write("END\n")
                fgro.write("%8.3f%8.3f%8.3f"%(0,0,0))
                fgro.close()
            if CGlevel["nucl"] > 1:
                self.nucl.S = det.get_S_beads(reslist=self.nucl.res,XYZ=self.nucl.xyz,position=nucl_pos["S"])
                if CGlevel["nucl"] == 3:
                    self.nucl.B = dict()
                    self.nucl.B.update(det.get_B_beads(reslist=self.nucl.res,XYZ=self.nucl.xyz,position=[nucl_pos["Bpy"]],Btype="UTC"))
                    self.nucl.B.update(det.get_B_beads(reslist=self.nucl.res,XYZ=self.nucl.xyz,position=[nucl_pos["Bpu"]],Btype="AG"))
                    temp_keys = list(self.nucl.B.keys()); temp_keys.sort()
                    self.nucl.B = {k:self.nucl.B[k] for k in temp_keys}
                if CGlevel["nucl"] == 5:
                    #___WIP___#
                    print ("Sorry, 5-bead model is still work in progress. Stay tuned for updates")
                    exit()
                #for x in self.nucl.B: print (x,self.nucl.B[x])
                self.nucl.B_atn,self.nucl.S_atn = dict(),dict()
                self.nucl.sc_file = ".".join(self.nucl.pdbfile.split(".")[:-1]+["native_P-S-B.pdb"])
                with open(self.nucl.sc_file,"w+") as fout:
                    fgro = open(nucl_grofile,"w+")
                    fgro.write("CG file %s for GROMACS\n"%(nucl_grofile))
                    fgro.write("%d\n"%(len(self.nucl.P)+len(self.nucl.S)+sum([len(self.nucl.B[x]) for x in self.nucl.B])))
                    atcount,prev_chain = 0,0
                    for res in self.nucl.P:
                        if res[0]!=prev_chain: fout.write("TER\n")
                        self.nucl.P_atn[res] = atcount
                        atcount+=1
                        line = "ATOM".ljust(6)+hy36encode(5,atcount)+" "+"P".center(4)+" "+res[-1].rjust(3)+" "+self.nucl.cid[res[0]]+hy36encode(4,res[1])+4*" "+3*"%8.3f"%tuple(self.nucl.P[res])
                        fout.write(line+"\n")
                        line = str(res[1]).rjust(5)+res[-1].ljust(5)+"P".center(5)+hy36encode(5,atcount).rjust(5)+3*"%8.3f"%tuple(0.1*self.nucl.P[res])
                        fgro.write(line+"\n")
                        if res not in self.nucl.S_atn: self.nucl.S_atn[res],self.nucl.B_atn[res] = [],[]
                        self.nucl.S_atn[res].append(atcount)
                        atcount+=1
                        line = "ATOM".ljust(6)+hy36encode(5,atcount)+" "+str("C0'").center(4)+" "+res[-1].rjust(3)+" "+self.nucl.cid[res[0]]+hy36encode(4,res[1])+4*" "+3*"%8.3f"%tuple(self.nucl.S[res])
                        fout.write(line+"\n")
                        line = str(res[1]).rjust(5)+res[-1].ljust(5)+str("C0'").center(5)+hy36encode(5,atcount).rjust(5)+3*"%8.3f"%tuple(0.1*self.nucl.S[res])
                        fgro.write(line+"\n")
                        for x in range(len(self.nucl.B[res])):
                            self.nucl.B_atn[res].append(atcount)
                            atcount+=1
                            line = "ATOM".ljust(6)+hy36encode(5,atcount)+" "+str("N"+str(x)).center(4)+" "+res[-1].rjust(3)+" "+self.nucl.cid[res[0]]+hy36encode(4,res[1])+4*" "+3*"%8.3f"%tuple(self.nucl.B[res][x])
                            fout.write(line+"\n")
                            line = str(res[1]).rjust(5)+res[-1].ljust(5)+str("N"+str(x)).center(5)+hy36encode(5,atcount).rjust(5)+3*"%8.3f"%tuple(0.1*self.nucl.B[res][x])
                            fgro.write(line+"\n")
                        prev_chain = res[0]
                    fout.write("END\n")
                    fgro.write("%8.3f%8.3f%8.3f"%(0,0,0))
                    fgro.close()

        if len(self.nucl.lines) != 0:
            if len(self.prot.lines) != 0:
                self.__combineGro__(outfile=outgro)

    def extractPDBSegment(self,fasta,data):
        #reading fasta and extracting segment from input PDB data
        outpdb = fasta+".pdb"
        chains,chain_order = dict(),list()
        with open(fasta) as fin:
            for line in fin:
                line = line.strip()
                if len(line) == 0: continue
                elif line.startswith(">"):
                    tag = line.strip().strip(">").split(":")
                    tag = tag[:len(tag)]+[chr(65+len(chains)),1][len(tag)-1:]
                    tag=tuple(tag)
                    chains[tag] = str()
                    chain_order.append(tag)
                else: chains[tag] += line.strip().upper()

        with open(outpdb,"w+") as fout:
            for tag in chains:
                seg_seq=chains[tag]
                if seg_seq in data.nucl.seq: data,stype=data.nucl,"nucl"
                elif seg_seq in data.prot.seq: data,stype=data.prot,"prot"
                seq=data.seq.split()
                assert tag[1] in [data.cid[x] for x in np.where([seg_seq in x for x in seq])[0]], \
                    "Error, input segment chaind ID mismatch"
                index=np.where([data.cid[x]==tag[1] for x in np.where([seg_seq in x for x in seq])[0]])[0][0]
                name,c=tag[:2]
                r0=int(tag[2])
                if len(tag)==3: r1=r0+len(chains[tag])
                else: r1=int(tag[3])
                assert r1-r0==len(chains[tag]),\
                    "Error, chain length and resnum mismatch in %s"%fasta
                checkres={(c,r):0 for r in list(range(r0,r1+1))}
                for line in data.lines:
                    if line.startswith("ATOM"):
                        c,r=line[21],hy36decode(4,line[22:26])
                        if (c,r) in checkres: 
                            fout.write(line)
                            if line[12:16].strip()=="CA": checkres[(c,r)]+=1
                    if sum(checkres.values())==len(checkres): break

        self.pdbfile=self.__refinePDB__(infile=outpdb)
        self.__readPDB__()
        #if stype=="prot": self.prot.res=[tuple([index]+list(x[1:])) for x in self.prot.res]
        #if stype=="nucl": self.nucl.res=[tuple([index]+list(x[1:])) for x in self.nucl.res]
        self.segment_cidx=index
        return outpdb

    def buildProtIDR(self,fasta,rad,topbonds=False,CBgly=False):
        #reading fasta and writing stretched IDR to pdb
        outpdb = fasta+".pdb"
        chains,chain_order = dict(),list()
        with open(fasta) as fin:
            for line in fin:
                line = line.strip()
                if len(line) == 0: continue
                elif line.startswith(">"):
                    tag = line.strip().strip(">").split(":")
                    tag = tag[:len(tag)]+[chr(65+len(chains)),1][len(tag)-1:]
                    tag=tuple(tag)
                    chains[tag] = str()
                    chain_order.append(tag)
                else: chains[tag] += line.strip().upper()

        if topbonds:
            dist={tuple(1+pairs[x]):10*dist[x] for pairs,dist in topbonds for x in range(pairs.shape[0])}                
        else: assert len(rad)>0

        
        chain_width=max([3.9*len(chains[tag]) for tag in chain_order])
        assert chain_width < 2*(999.0),\
                "Strecthed structure for %s cannot be generated becuase of the chain length. Please build an input PDB with missing regions included using colabfold"%tag[0]

        
        amino_acid_dict={v:k for k,v in Prot_Data().amino_acid_dict.items()}
        with open(outpdb,"w+") as fout:
            ca_xyz = np.float_([-25*(len(chain_order)-1),chain_width/2,0])
            offset,chain_count,atnum,prev_ca = 0,0,0,0
            for tag in chain_order:
                if len(tag)==3: 
                    name,c=tag[:-1]
                    r0=int(tag[-1])
                    r1=r0+len(chains[tag])
                else:
                    name,c=tag[:2]
                    r0,r1=np.int_(tag[2:])
                    assert 1+r1-r0==len(chains[tag]),\
                        "Error, chain length and resnum mismatch in %s"%fasta
                resnum = list(range(r0,r1+1))
                prev_ca = 0
                for x in range(len(chains[tag])):
                    res = chains[tag][x]
                    atnum+=1
                    Arad,Brad = 10*rad["CA"],10*rad["CB"+res]
                    if prev_ca !=0:
                        if topbonds: ca_xyz = ca_xyz + np.float_([0,dist[(prev_ca,atnum)],0])*[-1,+1][chain_count%2]
                        else: ca_xyz = ca_xyz + np.float_([0,Arad+Arad,0])*[-1,+1][chain_count%2]
                    line = "ATOM".ljust(6)+hy36encode(5,atnum)+" "+"CA".center(4)\
                         +" "+amino_acid_dict[res]+" "+c[0].upper()+hy36encode(4,resnum[x]+offset)\
                         +4*" "+3*"%8.3f"%tuple(ca_xyz)
                    fout.write(line+"\n")
                    prev_ca=atnum
                    if not CBgly and res=="G":continue
                    atnum+=1
                    if topbonds: cb_xyz = ca_xyz + np.float_([0,0,dist[(prev_ca,atnum)]])*[-1,+1][x%2]
                    else: cb_xyz = ca_xyz + np.float_([0,0,Arad+Brad])*[-1,+1][x%2]
                    line = "ATOM".ljust(6)+hy36encode(5,atnum)+" "+"CB".center(4)\
                         +" "+amino_acid_dict[res]+" "+c[0].upper()+hy36encode(4,resnum[x]+offset)\
                         +4*" "+3*"%8.3f"%tuple(cb_xyz)
                    fout.write(line+"\n")
                    prev_cb=atnum
                fout.write("TER\n")
                chain_count+=1
                ca_xyz = ca_xyz + np.float_([50,0,0])
        self.pdbfile=self.__refinePDB__(infile=outpdb)
        self.__readPDB__()
        return outpdb