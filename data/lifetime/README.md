This folder contains the experiment data and scripts for VM lifetime, with the runs from May to June 2018 and in Feburary 2019.

#### Data

* The older runs are in us-east1-b with n1-standard-4 VM type. GPU instances are n1-standard-4 with 1 K80 equipped. Suffix '-less' means there's no stress workload imposed on this VM. Other VMs ran with `stress-ng` during the whole uptime with 90% CPU and 4 GB memory usage. 

* The newer runs have their zones specified by VM names. The meaning of '-less' suffix and lack thereof is same is above. K80 VMs have 4 vCPUs and 61 GB memory, P100 and V100 have 8 vCPUs and 61 GB memory.

* I used Google Sheets to process the duration: first convert the timestamps into epoch time, then do subtraction to get the length of duration in datetime format.

#### Scripts

* `lifetime.py` runs the experiments, and `plot.py` will give the result of `fig.3` in the paper. 