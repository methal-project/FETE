# Introduction

Not a real README, but we're testing the application and want to document it, so started taking notes here to create the real README.

# Application structure

- HOCR2ALTO: Scripts to convert between these formats. Can leave them in public app (maybe remove most of the outputs and leave one as an example?)
- ncrf: Andrew's neural CRF tests. Can remove it since didn't really exploit it
- sklearn_crfsuite: This is the main program. Most things happen here.
- utils.py: Useful to keep these in the public application
- example: some models, inputs and outputs for us to test and document things. Might leave something like this in the public repo

# Prediction

To generate TEI based on a directory of HOCR files, use the following command from within the `sklearn_crfsuite` directory:

```python main.py MODEL_PATH HOCR_DIRECTORY OUTPUT_TEI_PATH```

For instance:

```python main.py ../example/models/model-exp3-20221226.crf ../example/inputs/hocr-verbotte-fahne ../outputs/verbotte-fahne-exp3.xml```

This will predict the `verbotte-fahne-exp3.xml` TEI file based on HOCR at `../example/inputs/hocr-verbotte-fahne`

# Training

Training data consist on HOCR files and manually corrected TEI for them.

At the moment the training corpus is located at pre-defined directories inside `sklearn_crfsuite`:

- `html`: The HOCR (from which the features are computed)
- `tei`: The TEI (the labels to predict)

To train a model, use the following command from within `sklearn_crfsuite`:

```
python train.py html tei MODEL_OUTPUT_PATH
```

```
python train.py html tei ../example/models/model-exp3-new.crf
```

The `exp3` infix in the filename was used for the follwoing reason: Several feature combinations were implemented in the tool. The best one was called `exp3` and this model was trained with it, so we chose to include `exp3` in the filename (output file naming is manual)
