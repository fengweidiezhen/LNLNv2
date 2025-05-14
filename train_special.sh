for i in $(seq 1111 1 1113)
do
  CUDA_VISIBLE_DEVICES=0 python -u train.py --config_file configs/train_special.yaml --seed $i >./log/special.txt 2>&1 &
  wait
done
