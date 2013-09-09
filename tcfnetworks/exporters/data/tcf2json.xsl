<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
  version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xml="http://www.w3.org/XML/1998/namespace"
  xmlns:tcf="http://www.dspin.de/data/textcorpus"
  xmlns:str="http://exslt.org/strings"
  >

  <xsl:output
    method="text"
    encoding="utf-8"
    indent="yes" />

  <xsl:strip-space elements="*" />

  <xsl:template match="/">
{
  "nodes":[<xsl:apply-templates select="//tcf:graph/tcf:nodes/tcf:node"/>
  ],
  "links":[<xsl:apply-templates select="//tcf:graph/tcf:edges/tcf:edge"/>
  ],
  "text":[<xsl:apply-templates select="//tcf:sentences/tcf:sentence"/>
  ]
}
  </xsl:template>

  <xsl:template match="tcf:node">
    {"id":"<xsl:value-of select="@ID"/>",
     "name":"<xsl:value-of select="."/>"<xsl:if test="@class">,
     "class":"<xsl:value-of select="@class"/>"</xsl:if>,
     "tokens":[<xsl:for-each select="str:tokenize(@tokenIDs)">"<xsl:value-of select="."/>"<xsl:if test="position() != last()">,</xsl:if></xsl:for-each>]
    }<xsl:if test="position() != last()">,</xsl:if>
  </xsl:template>

  <xsl:template match="tcf:edge">
    {"id":"<xsl:value-of select="@ID"/>",
     "source":<xsl:variable name="source" select="@source"/><xsl:value-of select="count(//tcf:node[@ID=$source]/preceding-sibling::*)"/>,
     "target":<xsl:variable name="target" select="@target"/><xsl:value-of select="count(//tcf:node[@ID=$target]/preceding-sibling::*)"/><xsl:if test="@label">,
     "label":"<xsl:value-of select="@label"/>"</xsl:if><xsl:if test="@weight">,
     "weight":<xsl:value-of select="@weight"/></xsl:if>
    }<xsl:if test="position() != last()">,</xsl:if>
  </xsl:template>

  <xsl:template match="tcf:sentence">
    <xsl:variable name="tokens" select="//tcf:tokens"/>
    {"id":"<xsl:value-of select="@ID"/>",
     "tokens":[<xsl:for-each select="str:tokenize(@tokenIDs)">"<xsl:value-of select="translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>"<xsl:if test="position() != last()">,</xsl:if></xsl:for-each>],
     "words":[<xsl:for-each select="str:tokenize(@tokenIDs)">
        <xsl:variable name="tokenID" select="translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz')"/>
        <xsl:variable name="token" select="$tokens/tcf:token[@ID=$tokenID]"/>
       {"id":"<xsl:value-of select="$tokenID"/>",
        "text":"<xsl:value-of select="$token"/>"
       }<xsl:if test="position() != last()">,</xsl:if>
     </xsl:for-each>]
    }<xsl:if test="position() != last()">,</xsl:if>
  </xsl:template>

</xsl:stylesheet>
