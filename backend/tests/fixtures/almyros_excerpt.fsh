// Real excerpt from hl7-eu/oah almyros_gov_chem.fsh (Aluminium 2018) + water_tmp / ec_tmp point samples
// Used as a test fixture — values are official example literals, not invented.

Instance: Obs-Almyros-AluminiumDissolved-2018
Title: "Observation - Almyros Aluminium dissolved (2018 summary)"
Description: "Aggregated statistics for aluminium dissolved in the government chemical analysis (Almyros site, 2018)."
InstanceOf: ObservationWithCompOah
Usage: #example
* status = #final
* category[0] = http://terminology.hl7.org/CodeSystem/observation-category#laboratory "Laboratory"
* code = TemporaryOahSystem#aluminium-dissolved "Aluminium dissolved"
* code.text = "Aluminium dissolved"
* subject = Reference(Loc-Almyros)
* effectivePeriod.start = "2018-01-01"
* effectivePeriod.end = "2018-12-31"
* performer[0].display = "Hellenic Government Chemical Service"
* component[+].code = http://terminology.hl7.org/CodeSystem/observation-statistics#average "Average"
* component[=].valueQuantity = 50000 'ug/L' "microgram per liter"
* component[+].code = http://terminology.hl7.org/CodeSystem/observation-statistics#maximum "Maximum"
* component[=].valueQuantity = 100000 'ug/L' "microgram per liter"
* component[+].code = http://terminology.hl7.org/CodeSystem/observation-statistics#minimum "Minimum"
* component[=].valueQuantity = 100000 'ug/L' "microgram per liter"
* component[+].code = http://terminology.hl7.org/CodeSystem/observation-statistics#median "Median"
* component[=].valueQuantity = 10 'ug/L' "microgram per liter"

Instance: Obs-WaterTemp-Almyros-2025-04-14
Title: "Observation - Almyros water temperature (2025-04-14)"
Description: "Spring 2025 Almyros measurement for the OneAquaHealth pilot."
InstanceOf: ObservationIndicatorsOah
Usage: #example
* status = #final
* code = TemporaryOahSystem#waterTemperature "Water temperature"
* subject = Reference(Loc-Almyros)
* effectiveDateTime = "2025-04-14"
* performer.display = "OneAquaHealth Crete Lab"
* device = Reference(Dev-HI98130)
* valueQuantity = 16.2 'Cel' "Celsius"

Instance: Obs-EC-Almyros-2024-11-21
Title: "Observation - Almyros electrical conductivity (2024-11-21)"
Description: "Almyros conductivity reading collected in November 2024."
InstanceOf: ObservationIndicatorsOah
Usage: #example
* status = #final
* code = TemporaryOahSystem#conductivity "Conductivity"
* subject = Reference(Loc-Almyros)
* effectiveDateTime = "2024-11-21"
* performer.display = "OneAquaHealth Crete Lab"
* device = Reference(Dev-HI98130)
* valueQuantity = 18.4 'mS/cm' "mS/cm"

Instance: Obs-Benevento01-NO2-2018
Title: "Observation - Benevento01 NO2 (2018 summary)"
Description: "Should be filtered out of Almyros-only normalize."
InstanceOf: ObservationWithCompOah
Usage: #example
* status = #final
* code = TemporaryOahSystem#no2 "NO2"
* code.text = "NO2"
* subject = Reference(Loc-Benevento-01)
* effectivePeriod.start = "2018-01-01"
* effectivePeriod.end = "2018-12-31"
* component[+].code = http://terminology.hl7.org/CodeSystem/observation-statistics#median "Median"
* component[=].valueQuantity = 20 'ug/L' "microgram per liter"
