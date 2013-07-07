<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xml="http://www.w3.org/XML/1998/namespace"
  xmlns:tcf="http://www.dspin.de/data/textcorpus"
  xmlns:gexf="http://www.gexf.net/1.2draft"
  xmlns="http://www.gexf.net/1.2draft"
  exclude-result-prefixes="tcf">

  <xsl:output
    method="xml"
    encoding="utf-8"
    indent="yes" />

  <xsl:strip-space elements="*" />

  <xsl:template match="/">
    <gexf version="1.2">
      <graph mode="static" defaultedgetype="undirected">
        <xsl:if test="//tcf:graph/tcf:nodes/tcf:node[@class]">
          <attributes class="node">
            <attribute id="0" title="class" type="string"/>
          </attributes>
        </xsl:if>
        <nodes>
          <xsl:apply-templates select="//tcf:graph/tcf:nodes/tcf:node"/>
        </nodes>
        <edges>
          <xsl:apply-templates select="//tcf:graph/tcf:edges/tcf:edge"/>
        </edges>
      </graph>
    </gexf>
  </xsl:template>

  <xsl:template match="tcf:node">
    <node id="{ @ID }" label="{ . }">
      <xsl:if test="@class">
        <attvalues>
          <attvalue for="0" value="{ @class }"/>
        </attvalues>
      </xsl:if>
    </node>
  </xsl:template>

  <xsl:template match="tcf:edge">
    <edge id="{ @ID }" source="{ @source }" target="{ @target }">
      <xsl:if test="@label">
        <xsl:attribute name="label">
          <xsl:value-of select="@label" />
        </xsl:attribute>
      </xsl:if>
      <xsl:if test="@weight">
        <xsl:attribute name="weight">
          <xsl:value-of select="@weight" />
        </xsl:attribute>
      </xsl:if>
    </edge>
  </xsl:template>

</xsl:stylesheet>
