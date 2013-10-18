# SongYNC

SongYNC 可以帮助你在百度音乐、豆瓣 FM、虾米等音乐网站之间同步收藏的音乐。

目前支持从：

- 百度音乐
- 豆瓣电台

同步至：

- 虾米音乐

## 安装

推荐使用 [virtualenv](http://www.virtualenv.org)。

    $ git clone https://github.com/psjay/songync.git
    $ cd songync
    $ pip install -r requirements.txt

## 使用

    $ python sync.py [-h] -f {baidu | douban} -t {xiami}

## WTFPL

               DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
                       Version 2, December 2004

    Copyright (C) 2013 PSJay <psjay.peng@gmail.com>

    Everyone is permitted to copy and distribute verbatim or modified
    copies of this license document, and changing it is allowed as long
    as the name is changed.

               DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE
      TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION

     0. You just DO WHAT THE FUCK YOU WANT TO.
