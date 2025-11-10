# Stardew Valley Player Swap

This is a Python program that takes in a Stardew Valley save file, and lets you
swap the current player with one of the farmhands.  This is useful because it
lets you move the save file between different people.

This program was created because I was in a co-op farm with people in three
different time zones—US/Pacific, CET, and Australia/Brisbane—who had different
work schedules.  To maximize play time, we wanted to hand off the save file
between two different people.  The problem is, Stardew Valley assumes the
person hosting the game is the player.

It's important to note: **This is not perfect!** There are a number of issues
that I know about, and probably more that I *don't* know about.  Check out the
[GitHub Issues](https://github.com/akkornel/svswap/issues) to see what problems
I know about.  If you find an additional problem, you can make a note of it,
but **please do not expect me to fix problems!**  I only put this code out here
because it did not feel right to keep it to myself.  But at the same time, I
cannot say that it will work fine for you.

## Requirements

* Stardew Valley 1.6

  This code was developed against Stardew Valley 1.6.  If you last saved your
  game in an earlier version of Stardew Valley, the **current player** should
  upgrade to 1.6, then load and save the game (by sleeping).  Once the game has
  been saved with Stardew Valley 1.6, you can run this program.

* Python 3.8 or later

  This code was developed against Python 3.8.  Later versions should work.
  Earlier versions *might* work, but there's no guarantee!

* `lxml` 4.4.1 or later, and a compatible libxml2

  `lxml` is a Python wrapper around libxml2.  This is used for one important
  reason: Python's built-in `xml.etree.ElementTree` module has a problem with
  XML namespaces: The Stardew Valley saves use two XML namespaces—`xsd` and
  `xsi`—but only the `xsi` namespace is preserved properly when the XML is
  written out.

  The `lxml` modules properly preserve XML namespaces, so this package is
  required.  You can get it from PyPi, and if you use a distibution-packaged
  version of Python (like from a Linux distro, WSL2, Macports/Brew, etc.), you
  might have lxml available as a package.

* Pip 21.3 or later

  You don't technically need pip, but if you plan on installing lxml without
  using a distro package, then it's probably worth installing via pip.
