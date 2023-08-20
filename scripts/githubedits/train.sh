#!/bin/bash

source activate structural_edits
export CUDA_VISIBLE_DEVICES=0

# export PYTHONPATH=/scratch/yao.470/CMU_project/incremental_tree_edit:$PYTHONPATH
export PYTHONPATH=/root/projects/Graph2Edit:$PYTHONPATH

seed=7  # remember to change this!
config_file=$1
branch=$(git branch | sed -n -e 's/^\* \(.*\)/\1/p')
commit=$(git rev-parse HEAD | cut -c 1-7)
timestamp=`date "+%Y%m%d-%H%M%S"`
work_dir=exp_githubedits_runs/$(basename ${config_file})_branch_${branch}_${commit}.seed${seed}.${timestamp}

echo use config file ${config_file}
echo work dir=${work_dir}

mkdir -p ${work_dir}

# TODO 1: uncomment the training setting
# TODO 2: consider adding `--small_memory` to disable training data preprocessing
OMP_NUM_THREADS=1 python -u -m exp_githubedits train \
 	--cuda \
	--seed=${seed} \
	--work_dir=${work_dir} \
    ${config_file} 2>${work_dir}/err.log

#OMP_NUM_THREADS=1 python -u -m exp_githubedits imitation_learning \
#	--cuda \
#	--seed=${seed} \
#	--work_dir=${work_dir} \
#    ${config_file} 2>${work_dir}/err.log
