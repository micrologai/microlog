rm -rf ~/microlog/logs/*     

python3 examples/binaryTrees.py&
python3 examples/bookstore.py&
python3 examples/example.py&
python3 examples/go.py&
python3 examples/helloworld.py&
python3 examples/memory.py&
python3 examples/files.py&
python3 examples/modules.py&
python3 examples/dataframes.py&
python3 examples/threads.py&
python3 examples/startstop.py&

wait
wc  ~/microlog/logs/*/*.zip | sort -k 3         