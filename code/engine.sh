#!/bin/bash

# PARSE ARGUMENTS
if [ $# -eq 0 ]; then
    echo "No arguments supplied. "
    echo -e "\t" "\$1: experimental setting (mitmeto or ohnemeto)"
    echo -e "\t" "\$2: execute options (prepro, train, evaluate)"
    echo -e "\t" "\$3: number of repeats for train and evaluate"
    echo 'exiting...'
    exit
fi

experiment_name="reimp-"$1
echo 'experiment_name =' $experiment_name

options=$2
echo 'options =' $options

repeats=$3
echo 'repeats =' $repeats

# set train variable nn_components
if  [[ $experiment_name == *"mitmeto"* ]]; then
    nn_components="pem_lstm_metotype_attention"
elif  [[ $experiment_name == *"ohnemeto"* ]]; then
    nn_components="pem_lstm_attention"
else
    echo "Wrong arguments supplied: \$1=[mitmeto/ohnemeto]"
    exit
fi
echo 'nn_components =' $nn_components

# set train/evaluate variable distortion
if  [[ $experiment_name == *"contextdistorted"* ]]; then
    distortion="_contextdistorted_"
elif  [[ $experiment_name != *"distorted"* ]]; then
    distortion='_'
fi
echo 'distortion =' $distortion

# set variable strict
if  [[ $experiment_name == *"strictreordered"* ]]; then
    strict='strict'
else
    strict=''
fi 
echo 'strict =' $strict

if  [[ $experiment_name == *"extended"* ]]; then
    extended='extended'
else
    extended=''
fi 
echo 'extended =' $extended

# pre-processing
if  [[ $options == *"prepro"* ]]; then
    python3 -u -m preprocessing.prepro_util --experiment_name=$experiment_name
fi

# training
if  [[ $options == *"train"* ]]; then
    for v in `seq 1 $repeats`
    do
    python3 -u -m model.train  \
        --experiment_name=$experiment_name \
        --training_name=group_global/global_model_v$v \
        --nn_components=$nn_components \
        --train_datasets=combo_"$extended"_"$strict"reordered"$distortion"train  --ed_datasets=combo_"$extended"_"$strict"reordered"$distortion"dev \
        --evaluation_minutes=10 --nepoch_no_imprv=6 \
        --ed_val_datasets=0 \
        --ent_vecs_regularization=l2dropout  \
        --span_emb="boundaries"  --dim_char=50 --hidden_size_char=50 --hidden_size_lstm=150 \
        --fast_evaluation=True  \
        --attention_ent_vecs_no_regularization=True --final_score_ffnn=0_0 \
        --attention_R=10 --attention_K=100 \
        --global_thr=0.001 --global_score_ffnn=0_0
    done
fi

# evaluation
if  [[ $options == *"evaluate"* ]]; then
    for v in `seq 1 $repeats`
    do
    python -u -m model.evaluate \
        --training_name=group_global/global_model_v$v \
        --experiment_name=$experiment_name \
        --ed_datasets=combo_"$extended"_"$strict"reordered"$distortion"test_z_aida_test \
        --ed_val_datasets=0  --el_datasets=""  --el_val_datasets=0
    done
fi

echo 'OK'
