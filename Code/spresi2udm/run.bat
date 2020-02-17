python spresi2udm.py ..\..\Data\SPRESI\spresi-sample.rdf spresi-10k.xml
xmllint --schema ..\..\udm_6_0_0.xsd --noout spresi-10k.xml
