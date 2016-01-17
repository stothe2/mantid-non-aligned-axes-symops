# mantid-non-aligned-axes-symops

## To think about

1. Switch to using `SymmetryOperationFactory` for generating symmetry operation vectors instead of manually storing matrices and carring out matrix multiplication. See [here](http://docs.mantidproject.org/nightly/concepts/SymmetryGroups.html). However, note that when you call function `subscribedSymbols()`, you'll see that not all symmetry operations are listed. A way around this is to register all symmetry operations beforehand (that is, in `PyInit` section of the algorithm).
2. Instead of having the user to enter the space group, create a list of all symmetry operations (there are only a few dozen or so), and allow the user to select them through a GUI.
3. Normalization.


## Work in-progress

1. Handling exceptions. Would eventually need to make appropriate changes to `MantidKernal/Exception.h`.
2. Make the code more user-friendly by allowing users to select which symmetry operations they want to use through a GUI. Look at [`VisibleWhenProperty`](http://docs.mantidproject.org/nightly/api/python/mantid/kernel/VisibleWhenProperty.html) and [`EnabledWhenProperty`](http://docs.mantidproject.org/nightly/api/python/mantid/kernel/EnabledWhenProperty.html). Current version of Mantid source code doesn't allow multiple property settings, and only the last one is used. Any way around this issue?
3. Write test cases.

## Running the code

Load the script in Mantid, and execute it. After execution, you should see `SpaceGroupSymOps` in the algorithm selector box under the section `PythonAlgorithms`. After you've loaded all data files and have a `MDWorkspace`, run the algorithm by double-clicking on the name.

Alternately, you can use the command-line. See [this](http://www.mantidproject.org/Running_Algorithms_With_Python) for more information.
