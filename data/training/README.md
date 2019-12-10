This folder contains data and scripts to run all the experiments on K80,P100,V100 cluster and single worker training, as well as cross-region training.

#### Data

The folders are grouped into different experiment categories.
* `experiment_1ps_vs_2ps` contains data that shows the training performance bottleneck imposed by PS(Fig.6)
	* `1ps_k80` has the data for 1 parameter server and 2-8 workers.
	* The other folders are named `XpsYZ`, where X denotes the numer of parameter servers, Y number of workers and Z type of GPU.
* `experiment_cross_region` contains data of mixed region training(III.G and fig.7)
	* The folders are named `XeYcZw`, where X is the number of workers in us-east, Y us-central and Z us-west.
	* Suffix '-p100' means the experiment was done using P100 GPU, otherwise it used K80 GPU
* `experiment_mixed_gpu` contains data of mixed GPU training(III.G and fig.8)
	* Folders are named `XvYpZk`, where X is the number of V100 workers, Y P100 workers and Z K80 workers.
* `k80_on_demand` contains data for experiments conducted using on demand K80 GPU workers.
* `k80_spot` contains data for experiments conducted using spot K80 GPU workers.
* `p100_v100_spot` contains data for experiments conducted using spot P100 and V100 GPU workers respectively. 

#### Scripts

In the `code` directory:
* `training_data_fetcher.py` uses TensorBoard API to process the raw training data from checkpoints saved to Google storage. Specify target path and file destination to use it. Note: this cannot run on my MacBook reporting numpy version errors despite that I have the correct version installed. I used this on a VM.
* `data_processor.py` can process formatted data fetched by the `training_data_fetcher.py` as well as the VM data from sqlite3 database. `write_file()` will parse database entry and get VM role, start time, termination time, termination reason etc. `train_data_processor()` will process the raw checkpoint data into finalized data for plotting. `process_cost()` will separately generate the cost of training from the finalized data into `cost.csv` for plotting. `heatmap_data_generator()` is scratched right now.
* `resource_acquisition.py` handles the cluster creation request and built a GCE cluster accordingly.
* `start_training.sh`, `start_training_server.sh`, `stop_training.sh` are modified from Google Cloud ML Engine examples, and used for start training jobs on the created cluster. They should not be called directly.
* `datastore.py` is used to store the status of transient servers into a sqlite3 database.
* `training_job.py` wraps resource aquisition and job definition, and provides a monitoring mechanism to record the status of transient workers. It can also be used to run on demand jobs by passing `preemptible=False`. It can also run heterogeneous jobs by passing `gpu_array` and `zone_array`, for example, a `gpu_array` of ['k80','k80','v100'] means we want three workers, the master(first element) and one worker with K80 GPU, the second worker with P100 GPU. For `zone_array`, we also need to pass the zone for parameter servers, for example, a cluster a 3 workers(master and 1 worker in us-east1-c, the other in us-west1-b) and 2 parameter servers(both in europe-west1-b) would have the array as ['us-east1-c','us-east1-c','us-west1-b','europe-west1-b','europe-west1-b']
* `heatmap.py` generates heatmap used in fig.1 and fig.4 in the paper. 