# Wynncraft Eco Optimiser
Welcome to my first ever public repo!!

This program optimises the production of your territories given certain weights and constraints.

I was able to run the entire maps eco in ~10 sec on my laptop, so as long as you're not using a toaster, 
this should work for pretty much any use case.

Also, so far I've mainly focussed on the optimiser itself, but I will make this more user friendly.

---
## How to use:

To use the optimiser, you need python3 and some packages (imaging a list here).

Then just run it by running the main.py file. This is also where you (will) configure most options.

The optimiser will then spit out a file output.json, which you can either try reading manually, or more easily, import it into [**this website**](https://fa-rog.github.io/economy/)!

---
## Options:

There are two input options:
1. Select a guild a headquarters location and the program will pull the territory data from the wynncraft API.
Additionally, you can locate a file called presets.json in the data/ folder. Here you can set certain upgrade presets
to your territories, depending on conditions like the distance from HQ, etc. I did some default loadouts for now.
2. Choose territories and upgrades on again [**this website**](https://fa-rog.github.io/economy/) and export. 
This can be used as an input for the program.

Some more options that haven't been made easily accessible yet are individual weights, 
by which the optimiser should prioritize bonus resources and surplus supplies of each resource that you want.
