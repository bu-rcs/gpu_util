
if [[ $* == *"-j"* ]]; then
	echo Job info
else
	qacct $* -j
fi



