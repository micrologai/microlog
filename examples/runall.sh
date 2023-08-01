rm -rf ~/microlog/logs/*     

python3 examples/binaryTrees.py 2>&1 | grep "📈 Microlog" &
python3 examples/bookstore.py 2>&1 | grep "📈 Microlog" &
python3 examples/example.py 2>&1 | grep "📈 Microlog" &
python3 examples/go.py 2>&1 | grep "📈 Microlog" &
python3 examples/helloworld.py 2>&1 | grep "📈 Microlog" &
python3 examples/memory.py 2>&1 | grep "📈 Microlog" &
python3 examples/files.py 2>&1 | grep "📈 Microlog" &
python3 examples/modules.py 2>&1 | grep "📈 Microlog" &
python3 examples/dataframes.py 2>&1 | grep "📈 Microlog" &
python3 examples/threads.py 2>&1 | grep "📈 Microlog" &
python3 examples/startstop.py 2>&1 | grep "📈 Microlog" &

wait
wc  ~/microlog/logs/*/*.zip | sort -k 3         