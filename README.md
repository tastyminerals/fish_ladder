# fish_ladder
Simple console client to check BW ladder stats on Korean "Fish" server.

### Usage
`python2 fish_ladder.py -h` or `./fish_ladder.py -h`
```
usage: fish_ladder.py [-h] [-t TOP] [-p PLAYER] [-pls] [-u]

Query fish server and get the relevant information about BW players.

optional arguments:
  -h, --help            show this help message and exit
  -t TOP, --top TOP     Specify the number of top players to be displayed,
                        default = 20.
  -p PLAYER, --player PLAYER
                        Display information about specific player using
                        hisnickname. It can be a real nickname or fish
                        nickname.
  -pls, --players       Display a list of currently known BW players.
  -u, --update          Fetch most recent data from tl.wiki and fish.
  ```



### Examples
`./fish_ladder.py`

![0](http://i.imgur.com/i5rDwyh.png)

`./fish_ladder.py -t 5`

![1](http://i.imgur.com/YXx4nsi.png)

`./fish_ladder.py -p Zeus`

![2](http://i.imgur.com/0IjaEXB.png)

`./fish_ladder.py -p david`

![3](http://i.imgur.com/24TBl4R.png)
