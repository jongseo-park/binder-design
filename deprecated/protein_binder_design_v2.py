#!/usr/bin/env python3

# Script for designing protein binder
# Miniproteins in this repository is originated from the supplementary data in Cao et al., (2022). Nature. 605, 551-560 

import os
import random
import string
import argparse

import time
from multiprocessing import Pool

from pymol import cmd
import pandas as pd
import numpy as np

parser = argparse.ArgumentParser (description='Script for designing protein binder')


# basic
parser.add_argument('--template', required=False, type=str, default='./templates/my.pdb', help='template file')
parser.add_argument('--binderdir', required=False, type=str, default='./binders/', help='path to binders')
parser.add_argument('--np', required=False, type=str, default='4', help='num cores')
parser.add_argument('--ops', required=False, type=str, default='mac', help='mac or linux')
parser.add_argument('--nstruct', required=False, type=int, default=1, help='nstruct argument for PatchDock')

# list
parser.add_argument('--minilist', required=False, type=str, default='./binders.list', help='list file' )
parser.add_argument('--reslist', required=False, type=str, default='./res.list', help='residue list file for PatchDock' )

# path
parser.add_argument('--danpath', required=False, type=str, default='/opt/tools/DeepAccNet/', help='Path to DeepAccNet')
parser.add_argument('--mpnnpath', required=False, type=str, default='/opt/tools/ProteinMPNN/', help='path to ProteinMPNN')
parser.add_argument('--patchdockpath', required=False, type=str, default='/opt/tools/PatchDock/', help='path to PatchDock')

# conda
parser.add_argument('--prodigyconda', required=False, type=str, default='prodigy', help='Name of conda env for PRODIGY')
parser.add_argument('--danconda', required=False, type=str, default='dan', help='Name of conda env for DeepAccNet')
parser.add_argument('--mpnnconda', required=False, type=str, default='proteinmpnn', help='Name of conda env for ProteinMPNN')

# dir
parser.add_argument('--inpdir', required=False, type=str, default='./00_inputs', help='saving path to prepared input files for docking')
parser.add_argument('--paramdir', required=False, type=str, default='./01_patchdock', help='saving path to prepared input files for docking')
parser.add_argument('--dockdir', required=False, type=str, default='./02_docking_files', help='saving path to docking files')
parser.add_argument('--designdir', required=False, type=str, default='./03_seq_design_files', help='saving path to designed sequences')
parser.add_argument('--packerdir', required=False, type=str, default='./04_packed_files', help='saving path to packed PDB files')
parser.add_argument('--minimdir', required=False, type=str, default='./05_minimized_files', help='saving path to minimized files')
parser.add_argument('--dandir', required=False, type=str, default='./09_DAN', help='saving path to binder files for DeepAccNet')

# etc
parser.add_argument('--danresult', required=False, type=str, default='./09_DAN/DAN_results.csv', help='Name of result csv file of DeepAccNet')
parser.add_argument('--sorting', required=False, type=str, default='score', help='Sort by ...')
parser.add_argument('--design_after_design', required=False, type=str, default='true', help='Run design twice')
parser.add_argument('--score', required=False, type=str, default='./final_score.txt', help='Scorefile to be converted to csv format')
parser.add_argument('--csvname', required=False, type=str, default='./final_score.csv', help='Name of converted csv file')
parser.add_argument('--dist', required=False, type=str, default='./10_results_pdb', help='directory to final results')

# additional fn
parser.add_argument('--prodigyrun', required=False, type=str, default='false', help='Run PRODIGY or not (true/false)')
parser.add_argument('--fn', required=False, type=str, default='', help='type a function name to use')
parser.add_argument('--postsele', required=False, type=str, default='false', help='')


args = parser.parse_args()

# -


def listgen (binderdir=args.binderdir, minilist=args.minilist):

    list_path = os.listdir(binderdir)
    pdb_list_path = [file for file in list_path if file.endswith('.pdb')]

    minilist = minilist.replace('./', '')
    minilist = minilist.replace('/', '')

    if minilist in os.listdir ('./'):
        print(f'**-----Please remove the {minilist} file-----**')
        exit()
       
    miniprotein_list = open (f'{minilist}', 'a')

    binderdir = binderdir.replace('./', '')
    binderdir = binderdir.replace('/', '')

    for i in pdb_list_path:
        miniprotein_list.write (f'{binderdir}/{i}' + '\n')


def patch_dock (template=args.template, minilist=args.minilist, paramdir=args.paramdir, patchdock=args.patchdockpath, reslist=args.reslist):

    if paramdir in os.listdir('./'):
        pass
    else:
        os.mkdir(paramdir)

    # param generate
    ls = open (minilist)

    patchdock = os.path.abspath(patchdock)
    abs_path = os.path.abspath(template)
    res_list = os.path.abspath(reslist)

    for i in ls:
        j = i.split('/')[-1].replace('.pdb','').rstrip()
        binder_protein = os.path.abspath(i).rstrip()
        with open (f'{paramdir}/{j}.params', 'w') as param:
            param.write(f'receptorPdb {abs_path}' + '\n')
            param.write(f'ligandPdb {binder_protein}' + '\n')
            param.write(f'protLib {patchdock}/chem.lib' + '\n')
            param.write(f'log-file {j}.log' + '\n')
            param.write(f'log-level 0' + '\n')
            param.write(f'receptorSeg 10.0 20.0 1.5 1 0 1 0' + '\n')
            param.write(f'ligandSeg 10.0 20.0 1.5 1 0 1 0' + '\n')
            param.write(f'scoreParams 0.3 -5.0 0.5 0.0 0.0 1500 -8 -4 0 1 0' + '\n')
            param.write(f'desolvationParams 500.0 1.0' + '\n')
            param.write(f'clusterParams 0.1 4 2.0 3.0' + '\n')
            param.write(f'baseParams 4.0 13.0 2' + '\n')
            param.write(f'matchingParams 1.5 1.5 0.4 0.5 0.9' + '\n')
            param.write(f'matchAlgorithm 1' + '\n')
            param.write(f'receptorGrid 0.5 6.0 6.0' + '\n')
            param.write(f'ligandGrid 0.5 6.0 6.0' + '\n')
            param.write(f'receptorMs 10.0 1.8' + '\n')
            param.write(f'ligandMs 10.0 1.8' + '\n')
            param.write(f'receptorActiveSite {res_list}' + '\n')

            param.close()

    # docking
    cmd_ls = []

    for i in os.listdir(f'{paramdir}'):
        outs = i.replace('.params','.out')
        cmd = f'{patchdock}/patch_dock.Linux {i} {outs}'
        cmd_ls.append(str(cmd))

    return cmd_ls


def mprun(i):
    os.system(i)


def gen_pdb(paramdir=args.paramdir, dockdir=args.dockdir, patchdock=args.patchdockpath, nstruct=args.nstruct):

    filels = os.listdir(paramdir)
    out_ls = [file for file in filels if file.endswith('.out')]

    if dockdir in os.listdir('./'):
        pass
    else:
        os.mkdir(dockdir)

    for i in out_ls:
        os.system(f'cp {paramdir}/{i} {dockdir}')

    os.chdir(dockdir)

    for i in out_ls:
        os.system(f'perl {patchdock}/transOutput.pl {i} 1 {nstruct}')
    os.chdir('../')

    os.system(f'rm -rf {dockdir}/*.out')


def design (mpnnpath=args.mpnnpath, mpnnconda=args.mpnnconda, designdir=args.designdir, dockdir=args.dockdir):
    shscript=f"""
#!/bin/bash

folder_with_pdbs="$1"

output_dir="$2"
if [ ! -d $output_dir ]
then
    mkdir -p $output_dir
fi


path_for_parsed_chains=$output_dir"/parsed_pdbs.jsonl"
path_for_assigned_chains=$output_dir"/assigned_pdbs.jsonl"
path_for_fixed_positions=$output_dir"/fixed_pdbs.jsonl"
chains_to_design="A"
#The first amino acid in the chain corresponds to 1 and not PDB residues index for now.
fixed_positions=""
# fixed_positions="1 2 3 4 5 6 7 8 23 25, 10 11 12 13 14 15 16 17 18 19 20 40" #fixing/not designing residues 1 2 3...25 in chain A and residues 10 11 12...40 in chain C

python {mpnnpath}/vanilla_proteinmpnn/helper_scripts/parse_multiple_chains.py --input_path=$folder_with_pdbs --output_path=$path_for_parsed_chains

python {mpnnpath}/vanilla_proteinmpnn/helper_scripts/assign_fixed_chains.py --input_path=$path_for_parsed_chains --output_path=$path_for_assigned_chains --chain_list "$chains_to_design"

python {mpnnpath}/vanilla_proteinmpnn/helper_scripts/make_fixed_positions_dict.py --input_path=$path_for_parsed_chains --output_path=$path_for_fixed_positions --chain_list "$chains_to_design" --position_list "$fixed_positions"

python {mpnnpath}/vanilla_proteinmpnn/protein_mpnn_run.py \
        --jsonl_path $path_for_parsed_chains \
        --chain_id_jsonl $path_for_assigned_chains \
        --fixed_positions_jsonl $path_for_fixed_positions \
        --out_folder $output_dir \
        --num_seq_per_target 1 \
        --sampling_temp "0.1" \
        --batch_size 1
"""

    designdir = designdir.replace('./', '')
    designdir = designdir.replace('/', '')

    if designdir in os.listdir('./'):
        pass

    else:
        os.mkdir(designdir)

    mp = open(f'./{designdir}/mpnn.sh', 'w')
    mp.write(shscript)
    mp.close()

    print ('-----------------------------')
    print ('ProteinMPNN running ...')

    os.system(f'chmod +x ./{designdir}/mpnn.sh')
    os.system(f'conda run -n {mpnnconda} ./{designdir}/mpnn.sh {dockdir} ./{designdir}')
    os.system(f'rm -rf ./{designdir}/mpnn.sh')



    design_list = os.listdir(f'./{designdir}/seqs/')
    fasta_list = [file for file in design_list if file.endswith('.fa') ]

    df1 = pd.DataFrame(columns=['description', 'score', 'recovery'])

    for i in fasta_list:
        with open (f'./{designdir}/seqs/{i}', 'r') as file:

            fa_header = file.readlines()[2]

            recov = fa_header.rstrip().split(',')[-1].split('=')[-1]
            score = fa_header.rstrip().split(',')[-2].split('=')[-1]

            df2 = pd.DataFrame([[i, score, recov]], columns=['description', 'score', 'recovery'])

            df1 = pd.concat([df1, df2], ignore_index=True)

            df1_newname = i.replace('.fa', '_packer_0001_minimize_0001')
            df1 = df1.replace({'description' : i}, df1_newname)

            # df1 = df1.append(pd.DataFrame([[i, score, recov]], columns=['name', 'score', 'recovery']), ignore_index=True)

    df1.to_csv(f'./{designdir}/seqs/design_result_merged.csv')



def packer (designdir=args.designdir, dockdir=args.dockdir, packerdir=args.packerdir, num_core=args.np, ops=args.ops):
    
    designdir = designdir.replace('./', '')
    designdir = designdir.replace('/', '')

    dockdir = dockdir.replace('./', '')
    dockdir = dockdir.replace('/', '')

    packerdir = packerdir.replace('./', '')
    packerdir = packerdir.replace('/', '')

    ops = ops.lower()
    
    if ops == 'mac':
        fixbb = 'fixbb.mpi.macosclangrelease'
    else:
        fixbb = 'fixbb.mpi.linuxgccrelease'

    if packerdir in os.listdir('./'):
        pass

    else:
        os.mkdir(packerdir)

    mpnn_list = os.listdir(f'./{designdir}/seqs/')

    for i in mpnn_list:
        with open (f'./{designdir}/seqs/{i}', 'r') as fasta:
            seqs = fasta.readlines()[3].rstrip()
            seqs = list(seqs)
            with open ('./resfile.txt', 'w') as resfile:
                resfile.write ('NATRO' + '\n')
                resfile.write ('start' + '\n')            
                for num, seq in enumerate (seqs):
                    resfile.writelines (str(num + 1) + f' A PIKAA {seq}' + '\n')
                
                resfile.close()
            fasta.close()    

        j = i.replace ('.fa', '.pdb')

        if num_core == 'all':
            os.system(f'mpirun --use-hwthread-cpus {fixbb} -in:file:s ./{dockdir}/{j} -in:file:fullatom -resfile resfile.txt -out:path:all {packerdir} -out:suffix _packer')

        else:
            os.system(f'mpirun -np {num_core} {fixbb} -in:file:s ./{dockdir}/{j} -in:file:fullatom -resfile resfile.txt -out:path:all {packerdir} -out:suffix _packer')

    os.system('rm -rf resfile.txt')

    packed_files = os.listdir(packerdir)
    packed_list_path = [file for file in packed_files if file.endswith('.pdb')]

    lsfile = open (f'./{packerdir}/packer_pdb.list', 'a')

    for i in packed_list_path:
        lsfile.write (f'{packerdir}/{i}' + '\n')

    lsfile.close()


def minim_intana (packerdir=args.packerdir, minimdir=args.minimdir, num_core=args.np, ops=args.ops):
    xmlStr = f"""
<ROSETTASCRIPTS>

	<SCOREFXNS>
		<ScoreFunction name="beta_nov16" weights="beta_nov16" />
		
	</SCOREFXNS>

	<RESIDUE_SELECTORS>
	</RESIDUE_SELECTORS>

	<TASKOPERATIONS>
	</TASKOPERATIONS>

	<FILTERS>
	</FILTERS>

	<MOVERS>
		<AtomTree name="atomtree" docking_ft="true" />

        <MinMover name='minimize' jump='1' scorefxn='beta_nov16' chi='true' bb='false' bondangle='false' bondlength='false' cartesian='0' tolerance='0.001' />

		<InterfaceAnalyzerMover name="int_ana" packstat="true" interface_sc="true" interface="A_B" pack_separated="true" />
	</MOVERS>

	<PROTOCOLS>
    
		<Add mover="atomtree" />
		<Add mover="minimize" />
		<Add mover="int_ana" />
        
	</PROTOCOLS>

</ROSETTASCRIPTS>
"""

    minimdir = minimdir.replace('./', '')
    minimdir = minimdir.replace('/', '')

    packerdir = packerdir.replace('./', '')
    packerdir = packerdir.replace('/', '')


    if minimdir in os.listdir('./'):
        pass

    else:
        os.mkdir(minimdir)

    f = open(f'./{minimdir}/minimize.xml', 'w')
    f.write(xmlStr)
    f.close()

    ops = ops.lower()

    if ops == 'mac':
        rosetta_scripts = 'rosetta_scripts.mpi.macosclangrelease'
    else:
        rosetta_scripts = 'rosetta_scripts.mpi.linuxgccrelease'

    if num_core == 'all':
        os.system(f'mpirun --use-hwthread-cpus {rosetta_scripts} -in:file:l ./{packerdir}/packer_pdb.list -out:path:all {minimdir} -out:suffix _minimize -parser:protocol ./{minimdir}/minimize.xml -out:file:scorefile score_minim.txt -corrections::beta_nov16 true')

    else:
        os.system(f'mpirun -np {num_core} {rosetta_scripts} -in:file:l ./{packerdir}/packer_pdb.list -out:path:all {minimdir} -out:suffix _minimize -parser:protocol ./{minimdir}/minimize.xml -out:file:scorefile score_minim.txt -corrections::beta_nov16 true')

    os.system(f'rm -rf ./{minimdir}/minimize.xml')



def dan (minimdir=args.minimdir, dandir=args.dandir, danpath=args.danpath, num_core=args.np, danconda=args.danconda):

    list_path = os.listdir(f'./{minimdir}/')
    pdb_list = [file for file in list_path if file.endswith('.pdb')]

    dandir = dandir.replace('\n', '')
    dandir = dandir.replace('./', '')
 
    if dandir in os.listdir('./'):
        pass
    else:
        os.mkdir(dandir)

      
    for i in pdb_list:
        binder = 'binder'
        cmd.load(f'./{minimdir}/{i}')
        cmd.create(binder, 'chain A')
        cmd.save(f'./{dandir}/{i}', f'{binder}')
        j = i.replace('.pdb','')
        cmd.remove(j)
        cmd.remove(binder)

    resultname = 'DAN_results.orig.csv'
    resultname_mod = 'DAN_results.csv'

    if num_core == 'all':
        num_core = 2 * (os.cpu_count()) - 2
    else:
        pass

    print ('-----------------------------')
    print ('DeepAccNet running ...')
    
    os.system(f'conda run -n {danconda} python3 {danpath}/DeepAccNet.py -r -v -pr --csv --process {num_core} {dandir} ./{dandir}/{resultname} > ./{dandir}/DAN_log.log')

    df = pd.read_csv(f'./{dandir}/{resultname}', delimiter=r'\s+')

    df.columns = ['description', 'plddt']

    # df_load = pd.DataFrame(df).sort_values(by=['plddt'], ascending=False).reset_index(drop=True)
    # df_load.to_csv(f'./{dandir}/{resultname_mod}')
    
    df.sort_values(by=['plddt'], ascending=False).reset_index(drop=True).to_csv(f'./{dandir}/{resultname_mod}')
    


def score_dan_merge (csvname=args.csvname, danresult=args.danresult):

    df1 = pd.read_csv(csvname)
    df2 = pd.read_csv(danresult)

    df_merge = pd.merge(df1, df2, on='description')

    df_merge = df_merge[['description','plddt','score','recovery','dSASA_int','dSASA_hphobic','dSASA_polar','hbonds_int','sc_value','total_score','complex_normalized','dG_cross','dG_cross/dSASAx100','dG_separated','dG_separated/dSASAx100','delta_unsatHbonds','dslf_fa13','fa_atr','fa_dun_dev','fa_dun_rot','fa_dun_semi','fa_elec','fa_intra_atr_xover4','fa_intra_elec','fa_intra_rep_xover4','fa_intra_sol_xover4','fa_rep','fa_sol','hbond_E_fraction','hbond_bb_sc','hbond_lr_bb','hbond_sc','hbond_sr_bb','hxl_tors','lk_ball','lk_ball_bridge','lk_ball_bridge_uncpl','lk_ball_iso','nres_all','nres_int','omega','p_aa_pp','packstat','per_residue_energy_int','pro_close','rama_prepro','ref','side1_normalized','side1_score','side2_normalized','side2_score']]
  
    csvname = csvname.replace('./', '')
    csvname = csvname.replace('/', '')

    csvname = csvname.replace('.csv','_plddt.csv')

    df_merge[df_merge.dSASA_int > 0].sort_values(by=['plddt'], ascending=False).reset_index(drop=True).to_csv(csvname)



def txt2csv (score=args.score, csvname=args.csvname, designdir=args.designdir):
    
    pd.read_csv(score, delimiter=r'\s+').to_csv(csvname)

    with open (csvname, 'r') as file:
        ls = file.readlines()
        with open (csvname, 'w') as newfile:
            for i, j in enumerate (ls):
                if i == 0:
                    pass
                else:
                    newfile.writelines(j)

    df = pd.read_csv(csvname)

    # desc_list = list(np.array(df['description'].tolist()))

    # for i in desc_list:
    #     newname = i[:-26]
    #     df = df.replace({'description' : i}, newname)

    # df = df[['description','dSASA_int','dSASA_hphobic','dSASA_polar','hbonds_int','total_score','complex_normalized','dG_cross','dG_cross/dSASAx100','dG_separated','dG_separated/dSASAx100','delta_unsatHbonds','dslf_fa13','fa_atr','fa_dun_dev','fa_dun_rot','fa_dun_semi','fa_elec','fa_intra_atr_xover4','fa_intra_elec','fa_intra_rep_xover4','fa_intra_sol_xover4','fa_rep','fa_sol','hbond_E_fraction','hbond_bb_sc','hbond_lr_bb','hbond_sc','hbond_sr_bb','hxl_tors','lk_ball','lk_ball_bridge','lk_ball_bridge_uncpl','lk_ball_iso','nres_all','nres_int','omega','p_aa_pp','packstat','per_residue_energy_int','pro_close','rama_prepro','ref','sc_value','side1_normalized','side1_score','side2_normalized','side2_score']]
    # df.to_csv('df_.csv')
    # df.sort_values(by=['dSASA_int'], ascending=False).reset_index(drop=True).to_csv(csvname)

    try:
        designdir = designdir.replace('./', '')
        designdir = designdir.replace('/', '')

        df2 = pd.read_csv (f'./{designdir}/seqs/design_result_merged.csv')

        df_merge = pd.merge(df, df2, on='description')

        df_merge = df_merge[['description','score','recovery','dSASA_int','dSASA_hphobic','dSASA_polar','hbonds_int','total_score','complex_normalized','dG_cross','dG_cross/dSASAx100','dG_separated','dG_separated/dSASAx100','delta_unsatHbonds','dslf_fa13','fa_atr','fa_dun_dev','fa_dun_rot','fa_dun_semi','fa_elec','fa_intra_atr_xover4','fa_intra_elec','fa_intra_rep_xover4','fa_intra_sol_xover4','fa_rep','fa_sol','hbond_E_fraction','hbond_bb_sc','hbond_lr_bb','hbond_sc','hbond_sr_bb','hxl_tors','lk_ball','lk_ball_bridge','lk_ball_bridge_uncpl','lk_ball_iso','nres_all','nres_int','omega','p_aa_pp','packstat','per_residue_energy_int','pro_close','rama_prepro','ref','sc_value','side1_normalized','side1_score','side2_normalized','side2_score']]

        df_merge[df_merge.dSASA_int > 0].sort_values(by=['score'], ascending=True).reset_index(drop=True).to_csv(csvname)

    except FileNotFoundError:
        df[df.dSASA_int > 0].sort_values(by=['dSASA_int'], ascending=False).reset_index(drop=True).to_csv(csvname)



def pdbsorting (csvname=args.csvname, minimdir=args.minimdir, dist=args.dist, postsele=args.postsele, sorting=args.sorting, designdir=args.designdir):

    if postsele == 'false':
        df = pd.read_csv(csvname).sort_values(by=[sorting], ascending=True)
    
    else:        
        df_orig = pd.read_csv(csvname)

        condition = (df_orig.plddt > 0.7) & (df_orig.dSASA_int > 900) & (df_orig.hbonds_int > 3)
        # condition = (df_orig.plddt > 0.7) & (df_orig.dSASA_int > 900) & (df_orig.hbonds_int > 3) & (df_orig.sc_value > 0.45)

        df = df_orig[condition].sort_values(by=['sc_value'], ascending=False).reset_index(drop=True)

        col_list = list(df.columns)
        col_list[0] = 'original_number'
        df.columns = col_list


    pdblist = df['description'].values.tolist()[0:200]

    csvname = csvname.replace('.csv', '')
    csvname = csvname.replace('./', '')
    csvname = csvname.replace('/', '')

    dist = dist.replace('./', '')
    dist = dist.replace('/', '')

    minimdir = minimdir.replace('./', '')
    minimdir = minimdir.replace('/', '')

    if postsele == 'false':
        pdbpath = 'rank_' + minimdir
        pass
    else:
        df.to_csv(f'{csvname}_selected.csv')
        pdbpath = 'Post_selected_rank_' + minimdir


    if dist in os.listdir('./'):
        pass
    else:
        os.mkdir(dist)


    if pdbpath in os.listdir(f'./{dist}'):
        pass
    else:
        os.mkdir(f'{dist}/{pdbpath}')

    if 'fastas' in os.listdir(f'./{dist}/{pdbpath}/'):
        pass
    else:
        os.mkdir(f'./{dist}/{pdbpath}/fastas')


    for i, j in enumerate (pdblist):
        i += 1
        m = j[:-26]
        os.system(f'cp ./{minimdir}/{j}.pdb ./{dist}/{pdbpath}/rank_{i}_in_{minimdir}_{j}.pdb')
        os.system(f'cp ./{designdir}/seqs/{m}.fa ./{dist}/{pdbpath}/fastas/rank_{i}_in_{minimdir}_{m}.fa')

    
def prodigy (minimdir=args.minimdir, csvname=args.csvname, prodigyconda=args.prodigyconda):
    print ('-----------------------------')
    print ('PRODIGY running ...')

    minimdir = minimdir.replace('./','')
    minimdir = minimdir.replace('/','')

    pdbs = os.listdir(minimdir)
    pdblist = [file for file in pdbs if file.endswith('.pdb')]

    df1 = pd.DataFrame({'name':[], 'pKd':[], 'pkcal':[]})


    for i in pdblist:
        os.system (f'conda run -n {prodigyconda} prodigy ./{minimdir}/{i} --selection A B > ./{minimdir}/temp.txt')
        
        with open (f'./{minimdir}/temp.txt', 'r') as pdgresult:
            pdg_lines = pdgresult.readlines()
            pKd = pdg_lines[-2].split(':')[-1].strip()
            pkcal = pdg_lines[-3].split(':')[-1].strip()

            if pkcal.replace('-','').replace('.','').isdigit() == True:
                pass
            else:
                pKd = 'NaN'
                pkcal = 'NaN'

            df2 = pd.DataFrame([[i, pKd, pkcal]], columns=['name', 'pKd', 'pkcal'])

            df1 = pd.concat([df1, df2], ignore_index=True)
        
    os.system(f'rm -rf ./{minimdir}/temp.txt')

    csvname = csvname.replace('.csv', '')
    csvname = csvname.replace('./','')
    csvname = csvname.replace('/','')

    df1.to_csv(f'{csvname}_E_calculated.csv')


# -


if __name__ == '__main__':

    start = time.time ()

    if args.fn == '':
        pass
    elif args.fn == 'listgen':
        listgen (binderdir=args.binderdir, minilist=args.minilist)
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()
    elif args.fn == 'patchdock':
        cmd_list = patch_dock (template=args.template, minilist=args.minilist, paramdir=args.paramdir, patchdock=args.patchdockpath, reslist=args.reslist)

        paramdir=args.paramdir
        os.chdir(paramdir)

        if args.np == 'all':
            nc = os.cpu_count() - 1
        else:
            nc = args.np

        p = Pool(processes=int(nc))
        rls = p.map(mprun, cmd_list)
        os.chdir('../')

        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()
    elif args.fn == 'gen_pdb':
        gen_pdb(paramdir=args.paramdir, dockdir=args.dockdir, patchdock=args.patchdockpath)
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()        
    elif args.fn == 'design':
        design (mpnnpath=args.mpnnpath, mpnnconda=args.mpnnconda, designdir=args.designdir, dockdir=args.dockdir)
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()        
    elif args.fn == 'packer':
        packer (designdir=args.designdir, dockdir=args.dockdir, packerdir=args.packerdir, num_core=args.np, ops=args.ops)
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()        
    elif args.fn == 'minim_intana':
        minim_intana (packerdir=args.packerdir, minimdir=args.minimdir, num_core=args.np, ops=args.ops)
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()        
    elif args.fn == 'txt2csv':
        txt2csv (score=args.score, csvname=args.csvname, designdir=args.designdir)
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()
    elif args.fn == 'pdbsorting':
        pdbsorting (csvname=args.csvname, minimdir=args.minimdir, dist=args.dist, postsele=args.postsele, sorting=args.sorting, designdir=args.designdir)
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()
    elif args.fn == 'prodigy':
        prodigy (minimdir=args.minimdir, csvname=args.csvname, prodigyconda=args.prodigyconda)
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()        
    elif args.fn == 'dan':
        dan (minimdir=args.minimdir, dandir=args.dandir, danpath=args.danpath, num_core=args.np, danconda=args.danconda)
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()  
    elif args.fn == 'score_dan_merge':
        score_dan_merge (csvname=args.csvname, danresult=args.danresult)
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()  
    else:
        print ('Please select one of the functions below and enter it.')
        print (
        '''
        listgen (binderdir, minilist)
        patch_dock (template, minilist, paramdir, patchdockpath, reslist)
        gen_pdb(paramdir, dockdir, patchdockpath, nstruct)
        design (mpnnpath, mpnnconda, designdir, dockdir)
        packer (designdir, dockdir, packerdir, np, ops)
        minim_intana (packerdir, minimdir, np, ops)
        txt2csv (score, csvname, designdir)
        pdbsorting (csvname, minimdir, dist, postsele, sorting, designdir)
        dan (minimdir, dandir, danpath, np, danconda)
        ((prodigy (minimdir, csvname, prodigyconda)))
        ((score_dan_merge (csvname, danresult)))
        '''
        )
        quit()

    
    if args.design_after_design == 'false':
        listgen (binderdir=args.binderdir, minilist=args.minilist)
        cmd_list = patch_dock (template=args.template, minilist=args.minilist, paramdir=args.paramdir, patchdock=args.patchdockpath, reslist=args.reslist)

        paramdir=args.paramdir
        os.chdir(paramdir)

        if args.np == 'all':
            nc = os.cpu_count() - 1
        else:
            nc = args.np

        p = Pool(processes=int(nc))
        rls = p.map(mprun, cmd_list)
        os.chdir('../')

        gen_pdb(paramdir=args.paramdir, dockdir=args.dockdir, patchdock=args.patchdockpath, nstruct=args.nstruct)
        design (mpnnpath=args.mpnnpath, mpnnconda=args.mpnnconda, designdir=args.designdir, dockdir=args.dockdir)
        packer (designdir=args.designdir, dockdir=args.dockdir, packerdir=args.packerdir, num_core=args.np, ops=args.ops)
        minim_intana (packerdir=args.packerdir, minimdir=args.minimdir, num_core=args.np, ops=args.ops)
        os.system(f'cp ./{args.minimdir}/score_minim.txt ./final_score.txt')
        txt2csv (score=args.score, csvname=args.csvname, designdir=args.designdir)
        if args.prodigyrun == 'true':
            prodigy (minimdir=args.minimdir, csvname=args.csvname, prodigyconda=args.prodigyconda)
        else:
            pass
        dan (minimdir=args.minimdir, dandir=args.dandir, danpath=args.danpath, num_core=args.np, danconda=args.danconda)
        score_dan_merge (csvname=args.csvname, danresult=args.danresult)
        pdbsorting (csvname='final_score_plddt.csv', minimdir=args.minimdir, dist='06_results_pdb', postsele=args.postsele, sorting='plddt', designdir=args.designdir)

        print ('Working done !')
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()     

    elif args.design_after_design == 'true':
        listgen (binderdir=args.binderdir, minilist=args.minilist)
        cmd_list = patch_dock (template=args.template, minilist=args.minilist, paramdir=args.paramdir, patchdock=args.patchdockpath, reslist=args.reslist)

        paramdir=args.paramdir
        os.chdir(paramdir)

        if args.np == 'all':
            nc = os.cpu_count() - 1
        else:
            nc = args.np

        p = Pool(processes=int(nc))
        rls = p.map(mprun, cmd_list)
        os.chdir('../')

        gen_pdb(paramdir=args.paramdir, dockdir=args.dockdir, patchdock=args.patchdockpath, nstruct=args.nstruct)
        design (mpnnpath=args.mpnnpath, mpnnconda=args.mpnnconda, designdir=args.designdir, dockdir=args.dockdir)
        packer (designdir=args.designdir, dockdir=args.dockdir, packerdir=args.packerdir, num_core=args.np, ops=args.ops)
        minim_intana (packerdir=args.packerdir, minimdir=args.minimdir, num_core=args.np, ops=args.ops)
        os.system(f'cp ./{args.minimdir}/score_minim.txt ./first_score.txt')
        txt2csv (score='first_score.txt', csvname='first_score.csv', designdir=args.designdir)
        if args.prodigyrun == 'true':
            prodigy (minimdir=args.minimdir, csvname='first_score.csv', prodigyconda=args.prodigyconda)
        else:
            pass
        design (mpnnpath=args.mpnnpath, mpnnconda=args.mpnnconda, designdir='06_seq_design_files_2', dockdir=args.minimdir)
        packer (designdir='06_seq_design_files_2', dockdir=args.minimdir, packerdir='07_packed_files_2', num_core=args.np, ops=args.ops)
        minim_intana (packerdir='07_packed_files_2', minimdir='08_minimized_files_2', num_core=args.np, ops=args.ops)
        os.system(f'cp ./08_minimized_files_2/score_minim.txt ./final_score.txt')
        txt2csv (score='final_score.txt', csvname='final_score.csv', designdir='06_seq_design_files_2')
        if args.prodigyrun == 'true':
            prodigy (minimdir='08_minimized_files_2', csvname='final_score.csv', prodigyconda=args.prodigyconda)
        else:
            pass
        dan (minimdir='08_minimized_files_2', dandir=args.dandir, danpath=args.danpath, num_core=args.np, danconda=args.danconda)
        score_dan_merge (csvname='final_score.csv', danresult=args.danresult)
        pdbsorting (csvname='final_score_plddt.csv', minimdir='08_minimized_files_2', dist=args.dist, postsele=args.postsele, sorting='plddt', designdir='06_seq_design_files_2')

        print ('Working done !')
        print ('Elapsed time: ', time.time() - start, 'sec')
        quit()        


    else:
        print ('Please specify the design_after_design argument as true/false')
