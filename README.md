FETE: Fast Encoding of Theater in TEI
=====================================
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10578269.svg)](https://doi.org/10.5281/zenodo.10578269)

# Introduction

FETE is an application to generate TEI for the body of theater plays in Alsatian, based on OCR output. It takes [HOCR](https://kba.github.io/hocr-spec/1.2/) or [ALTO](https://www.loc.gov/standards/alto/) formats as input. It outputs TEI for the play's body: `<div>` elements for acts and scenes (with the relevant `@type` attribute), as well as stage directions (`<stage>`) and character speech turns (`<sp>` elements and their children, also identifiying the `<speaker>` element). When speech is in verse, `<l>` elements are encoded.

The `<teiHeader>` element for the plays needs to be encoded separately, as does the play's `<castList>` element and other frontmatter preceding the play's first scene, besides backmatter after the last scene, if any exists.   

Inspired by earlier literature (e.g. [Grobid](https://grobid.readthedocs.io/en/latest/Introduction/) among others), the tool uses Conditional Random Fields (CRF) as implemented in [sklearn-crfsuite](https://github.com/TeamHG-Memex/sklearn-crfsuite). Lexical and typographical cues present in OCR output, besides token coordinates on the page, are exploited to generate TEI elements.  

The tool was developed by Andrew Briand (University of Washington), in the context of work supervised by Pablo Ruiz within the [Methal](https://methal.pages.unistra.fr) project (University of Strasbourg); the project is creating a large TEI-encoded corpus of theater in Alsatian varieties.

# Application structure

- `example`: example input, XML output obtained with it and CRF model used to predict the output.
- `hocr2alto`: Scripts to convert between HOCR and ALTO formats.
    - Usage is documented in the script
    - Requires the [`ocr-fileformat`](https://github.com/UB-Mannheim/ocr-fileformat) package
- `sklearn_crfsuite`: The main program is in this directory, see [Generating TEI](#prediction) and [Training a model](#training) below for its usage.
- `utils`: Some scripts for common manipulations to HOCR and TEI documents. Usage described in the scripts.

<a name="requirements"></a>
# Requirements

The tool requires the packages listed in [`requirements.txt`](./requirements.txt). To install them, you can run `pip install -r requirements.txt` from the directory where `requirements.txt` resides.

It is not required, but a good practice, to create a virtual environment for projects using the tool and install the requirements there. To create an environment, you can use [`venv`](https://docs.python.org/3/library/venv.html), or if you have [Anaconda](https://anaconda.org/anaconda/python), you can create it with `conda create --name fete python=3.12`, then activate the environment (`conda activate fete`) and run `pip install requirements.txt` once the environment is active.

<a name="prediction"></a>
# Generating TEI

To generate TEI based on a directory of HOCR files, use the following command from within the `sklearn_crfsuite` directory:

```
python main.py MODEL_PATH HOCR_DIRECTORY OUTPUT_TEI_PATH
```

For instance:

```
python main.py ../example/models/model-exp3-20221226.crf ../example/inputs/hocr-verbotte-fahne ../example/outputs/verbotte-fahne-exp3.xml
```

This will predict the `../example/outputs/verbotte-fahne-exp3.xml` TEI file based on HOCR at `../example/inputs/hocr-verbotte-fahne`

<a name="training"></a>

# Training a model

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

The `exp3` infix in the model filename was used for the follwoing reason: Several feature combinations were implemented in the tool. The best one was called `exp3` and this model was trained with it, so we chose to include `exp3` in the filename (output-file naming is manual)

# Postprocessing the output XML

Let's show this with an example. If you trained a model using the example command above and use it to predict TEI for `../example/input/hocr-verbotte-fahne`, your results should reproduce `../example/outputs/verbotte-fahne-exp3.xml`.

The prediction doesn't look bad, but you'll see it is not valid XML. This is because the model is designed to handle the plays' body, from the start of the first act to the final curtain, but not the front matter and back matter that may precede and follow those. Since we did not remove HOCR files for the front matter and back matter, the model tried to generate TEI from them, but this was expected to give errors. Once the portions generated based on the front matter and back matter are removed, the file will be valid XML. You can compare the file before and after by comparing `../example/outputs/verbotte-fahne-exp3.xml` with `../example/outputs/verbotte-fahne-exp3-postpro.xml`.

Instead of postprocessing the output XML by removing the front- and backmatter content, we could also remove the input HOCR files (or paragraphs if the body does not start and end on its own page) for such content before generating the XML output.

# Adapting to other languages

The lexical cues used by the tool are currently suitable for Alsatian theater. Paratext in Alsatian theater is often in German and sometimes in French. Accordingly, lexical cues are now provided in Alsatian varieties, besides German and French. 

The tool's lexical features (see [`sklearn_crfsuite/features.py`](./sklearn_crfsuite/features.py)) could be adapted to further languages. For training, a corpus of HOCR (or ALTO) plays and their corresponding TEI-encoding versions is needed (see [Training a model](#training) above).

# How to cite

The software may be cited as:

- Briand, Andrew & Ruiz Fabo, Pablo (2023). FETE: Fast Encoding of Theater in TEI.

You can also cite a related publication:

- Ruiz Fabo, Pablo, Bernhard, Delphine, Briand, Andrew & Werner, Carole. (2024). Computational drama analysis from almost zero electronic text: The case of Alsatian theater. To appear in Andresen, Melanie & Reiter, Nils (eds.). _Computational Drama Analysis: Reflecting Methods and Interpretations_. Preprint at https://univoak.eu/islandora/object/islandora:157880
