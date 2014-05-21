TCFnetworks
===========

TCFnetworks is a collection of tools that create networks (or: graphs) from annotated text corpora. This makes it possible to use methods from network analysis for corpus analysis.

One main goal for the development is compatibility with linguistic annotation services. The tools use [TCF] as data exchange format. They are based on [TCFlib] and meant to be run as web services, compatible with [WebLicht], or as command line programs.

[TCF]: http://weblicht.sfs.uni-tuebingen.de/weblichtwiki/index.php/The_TCF_Format
[TCFlib]: https://github.com/SeNeReKo/TCFlib
[WebLicht]: http://weblicht.sfs.uni-tuebingen.de/weblichtwiki/index.php/Main_Page

Why?
----

These tools are developed as part of the [SeNeReKo] project. They are meant to be a test bed to experiment with and compare different algorithms that create networks from texts. The resulting networks can be further analysed using standard procedures from network analysis.

[SeNeReKo]: http://senereko.ceres.rub.de

How?
----

For testing purposes, the easiest way to run the network tools is to use them as command line tools. They take an annotated TCF file as input and add a `graph` annotation layer. The most basic usage is this:

    annotators/cooccurrence.py < MyTCFFile.xml > MyTCFnetworkFile.xml

For compatibility with other applications for network analysis, exporters to standard network formats are provided:

    annotators/cooccurrence.py < MyTCFFile.xml | exporters/graphml > MyNetworkFile.graphml
