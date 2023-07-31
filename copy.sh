rm -rf zip

mkdir zip

mkdir zip/Treemap-Jupyter-Notebook/
mkdir zip/examples-binaryTrees/
mkdir zip/examples-bookstore/
mkdir zip/examples-dataframes/
mkdir zip/examples-example/
mkdir zip/examples-files/
mkdir zip/examples-go/
mkdir zip/examples-memory/
mkdir zip/examples-modules/
mkdir zip/setup/

cp /Users/laffra/microlog/logs/examples-binaryTrees/*.log zip/examples-binaryTrees
cp /Users/laffra/microlog/logs/examples-bookstore/*.log zip/examples-bookstore
cp /Users/laffra/microlog/logs/examples-dataframes/*.log zip/examples-dataframes
cp /Users/laffra/microlog/logs/examples-example/*.log zip/examples-example
cp /Users/laffra/microlog/logs/examples-files/*.log zip/examples-files
cp /Users/laffra/microlog/logs/examples-go/*.log zip/examples-go
cp /Users/laffra/microlog/logs/examples-memory/*.log zip/examples-memory
cp /Users/laffra/microlog/logs/examples-modules/*.log zip/examples-modules
cp /Users/laffra/microlog/logs/setup/*.log zip/setup

cd zip
ls -1 */* > ../logs