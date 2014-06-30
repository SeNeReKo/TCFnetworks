<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xml="http://www.w3.org/XML/1998/namespace"
  xmlns:tcf="http://www.dspin.de/data/textcorpus"
  xmlns:gexf="http://graphml.graphdrawing.org/xmlns"
  xmlns="http://graphml.graphdrawing.org/xmlns"
  exclude-result-prefixes="tcf">

  <xsl:output
    method="xml"
    encoding="utf-8"
    indent="yes" />

  <xsl:strip-space elements="*" />
  
  <xsl:template match="/">
    <graphml>
      <key id="label" for="node" attr.name="label" attr.type="string" />
      <xsl:if test="//tcf:graph/tcf:nodes/tcf:node[@class]">
        <key id="class" for="node" attr.name="class" attr.type="string" />
      </xsl:if>
      <xsl:if test="//tcf:graph/tcf:nodes/tcf:node[@type]">
        <key id="type" for="node" attr.name="type" attr.type="string" />
      </xsl:if>
      <xsl:if test="//tcf:graph/tcf:edges/tcf:edge[@label]">
        <key id="weight" for="edge" attr.name="label" attr.type="string" />
      </xsl:if>
      <xsl:if test="//tcf:graph/tcf:edges/tcf:edge[@weight]">
        <key id="weight" for="edge" attr.name="weight" attr.type="int" />
      </xsl:if>
      <graph edgedefault="undirected">
        <xsl:apply-templates select="//tcf:graph/tcf:nodes/tcf:node"/>
        <xsl:apply-templates select="//tcf:graph/tcf:edges/tcf:edge"/>
      </graph>
    </graphml>
  </xsl:template>

  <xsl:template match="tcf:node">
    <node id="{ @ID }">
      <data key="label"><xsl:value-of select="." /></data>
      <xsl:if test="@class">
        <data key="class"><xsl:value-of select="@class" /></data>
      </xsl:if>
      <xsl:if test="@type">
        <data key="type"><xsl:value-of select="@type" /></data>
      </xsl:if>
    </node>
  </xsl:template>

  <xsl:template match="tcf:edge">
    <edge id="{ @ID }" source="{ @source }" target="{ @target }">
      <xsl:if test="@label">
        <data key="label"><xsl:value-of select="@label" /></data>
      </xsl:if>
      <xsl:if test="@weight">
        <data key="weight"><xsl:value-of select="@weight" /></data>
      </xsl:if>
    </edge>
  </xsl:template>

</xsl:stylesheet>
