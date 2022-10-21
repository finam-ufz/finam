---
myst:
  html_meta:
    "description lang=en": |
      Top-level documentation for FINAM, with links to the rest of the site..
html_theme.sidebar_secondary.remove: true
---

# FINAM - is not a model

```{image} _static/logo.svg
:alt: FINAM Logo
:class: dark-light p-2
:width: 200px
:align: center
:target: https://finam.pages.ufz.de
```

FINAM is an open-source component-based model coupling framework for environmental models.
It aims at enabling bi-directional online couplings of models for different compartments like geo-, hydro-, pedo- and biosphere.

---

::::{grid} 1 2 2 3
:gutter: 1 1 1 2

:::{grid-item-card} {octicon}`book;1.5em;sd-mr-1` FINAM Book
:link: finam-book/index
:link-type: doc

Extensive User Guide to get in touch with FINAM.

+++
[Learn more »](finam-book/index)
:::

:::{grid-item-card} {octicon}`code-square;1.5em;sd-mr-1` Well documented API
:link: api/index
:link-type: doc

The API is designed to be as intuitive as possible and is thoroughly documented.

+++
[Learn more »](api/index)
:::

:::{grid-item-card} {octicon}`light-bulb;1.5em;sd-mr-1` Example Gallery
:link: https://git.ufz.de/FINAM/finam-examples
:link-type: url

See our gallery of examples that use FINAM.

+++
[Learn more »](https://git.ufz.de/FINAM/finam-examples)
:::

::::

---

## Resources

* FINAM [homepage](https://finam.pages.ufz.de)
* FINAM [documentation](https://finam.pages.ufz.de/finam/)
* FINAM [source code](https://git.ufz.de/FINAM/finam)
* FINAM [GitLab group](https://git.ufz.de/FINAM), containing further related projects

## FINAM Book

Information about using, configuration and exploring FINAM.

```{toctree}
:includehidden:
:maxdepth: 2
finam-book/index
```

## API References

Information about the API of FINAM.

```{toctree}
:maxdepth: 2
api/index
```
