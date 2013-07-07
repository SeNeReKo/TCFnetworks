TCFnetworks
===========

TCFnetworks is a collection of TCF compatible tools that creates networks (or: graphs) from annotated corpora. The tools are based on TCFlib and meant to be run as web services, compatible with [WebLicht], or as command line programs.

[WebLicht]: http://weblicht.sfs.uni-tuebingen.de/weblichtwiki/index.php/Main_Page

Why?
----

These tools are developed as part of the [SeNeReKo] project. They are meant as a test bed to experiment with and compare different algorithms that create networks from texts. The resulting networks can be further analysed using standard procedures from network analysis.

[SeNeReKo]: http://senereko.ceres.rub.de

How?
----

For testing purposes, the easiest way to run the network tools is to use them as command line tools. They take an annotated TCF file as input and add a `graph` annotation layer. Try this:

    cooccurrence.py < MyTCFFile.xml > MyTCFnetworkFile.xml
