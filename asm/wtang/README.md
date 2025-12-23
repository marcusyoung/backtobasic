# Spectrum Machine Language for the Absolute Beginner

Code related to the book "Spectrum Machine Language for the Absolute Beginner" edited by William Tang.

The `bas` folder contains BasinC file.

## EZCode

EZCode is a machine language editor. The programme listing is provided in the book. I started based on the tap file provided for downland by  [James O'Grady](https://www.youtube.com/watch?v=JkgZ4ehtTOw). I have made one main change. The original programme in the book uses the variable `ln` (for line number I think). However, **LN** is a keyword (the natural logarithm function) in Sinclair Basic. While that is allowed, BasinC doesn't like it and interprets 'ln' as the **LN** keyword. I have therefore changed `ln` to `lr`.

