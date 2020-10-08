: '
We attempt to replicate paper_models.
This script is created based on the readme page on github repo.
'
#python3 -m preprocessing.prepro_util --experiment_name=corefmerge

for v in 1
do
# batch_size=3 in the training_args.txt file in paper_models
python3 -m model.train  \
     --batch_size=4   --experiment_name=corefmerge \
     --training_name=group_global/global_model_v$v \
     --ent_vecs_regularization=l2dropout  --evaluation_minutes=10 --nepoch_no_imprv=6 \
     --span_emb="boundaries"  \
     --dim_char=50 --hidden_size_char=50 --hidden_size_lstm=150 \
     --nn_components=pem_lstm_attention_global \
     --fast_evaluation=True  \
     --attention_ent_vecs_no_regularization=True --final_score_ffnn=0_0 \
     --attention_R=10 --attention_K=100 \
     --train_datasets=aida_train \
     --ed_datasets=aida_dev_z_aida_test_z_aida_train --ed_val_datasets=0 \
     --global_thr=0.001 --global_score_ffnn=0_0           
done


# set the training_name argument appropriately
python3 -m model.evaluate \
      --training_name=group_global/global_model_v1 \
      --experiment_name=corefmerge \
      --ed_datasets=aida_test_z_combo_extended_strictreordered_test_z_combo_test   \
      --ed_val_datasets=0  --el_datasets=""  --el_val_datasets=0

