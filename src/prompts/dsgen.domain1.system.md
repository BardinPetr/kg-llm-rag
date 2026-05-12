SCENARIO DESCRIPTION:
Generate a knowledge graph representing a multi-layered corporate ownership
structure spanning several jurisdictions. The structure involves operating
companies, holding companies, trusts, and nominee arrangements. One or more
ultimate beneficiaries are subject to international sanctions. The scenario
should reflect realistic compliance investigation material: hidden ownership
chains, alias names, offshore registrations, and political exposure.

━━━━━━━━━━━━━━━━━━
ENTITY TYPES
━━━━━━━━━━━━━━━━━━
company
  A legal entity: LLC, JSC, Ltd, BV, GmbH, or similar.
  Has a jurisdiction, registration number, and legal form.

natural_person
  An individual human. May have aliases, multiple nationalities,
  political positions, or sanctions exposure.

trust
  A trust or private foundation holding assets or company shares.
  Different from a company — has a trustee and one or more beneficiaries.

jurisdiction
  A country or territory. Has a risk level for compliance purposes.

sanctions_list
  A published sanctions regime: OFAC SDN, EU Consolidated List,
  UN Security Council list, UK HMT list, etc.

sanction_entry
  A specific designation of a person or entity on a sanctions list.
  Has a program, a designation date, and legal basis.

political_position
  A formal government or state role: minister, deputy, governor, etc.

━━━━━━━━━━━━━━━━━━
RELATION FACT TYPES
(notation: subject --fact_type--> object)
━━━━━━━━━━━━━━━━━━
owned_by             company/trust --owned_by--> company/natural_person/trust
controlled_by        company/trust --controlled_by--> natural_person
directed_by          company --directed_by--> natural_person
registered_in        company/trust --registered_in--> jurisdiction
sanctioned_by        natural_person/company --sanctioned_by--> sanction_entry
listed_on            sanction_entry --listed_on--> sanctions_list
beneficiary_of       natural_person --beneficiary_of--> trust
trustee_of           natural_person --trustee_of--> trust
nominee_for          natural_person --nominee_for--> natural_person
family_member_of     natural_person --family_member_of--> natural_person
holds_position       natural_person --holds_position--> political_position
authorized_signatory natural_person --authorized_signatory--> company

━━━━━━━━━━━━━━━━━━
VALUE FACT TYPES
━━━━━━━━━━━━━━━━━━
For company:
  registration_number     official registration or tax ID
  legal_form              "ООО" / "ПАО" / "Ltd" / "B.V." etc.
  incorporation_date      YYYY-MM-DD
  registered_address      full address string
  ownership_percentage    "60%" — majority stake in its parent

For natural_person:
  nationality             country name
  date_of_birth           YYYY-MM-DD
  alias_name              alternative spelling or transliteration of name
  passport_series         document identifier

For trust:
  governing_law           jurisdiction whose law governs the trust
  establishment_date      YYYY-MM-DD

For jurisdiction:
  risk_level              "high" / "medium" / "low"
  fatf_status             "blacklist" / "greylist" / "standard"

For sanction_entry:
  sanction_program        e.g. "UKRAINE-EO13685", "RUSSIA-EO14024"
  designation_date        YYYY-MM-DD
  legal_basis             regulation or executive order reference

For political_position:
  position_title          full title of the role
  appointing_body         which authority appointed to this role

━━━━━━━━━━━━━━━━━━
REQUIRED CHAIN PATTERNS
Ensure your graph contains at least these structural patterns.
UIDs and names are your choice — the types and sequence are required.
━━━━━━━━━━━━━━━━━━
CHAIN A (depth 4 — core UBO + sanctions chain):
(company) --owned_by-->
(company) --owned_by-->
(trust) --controlled_by-->
(natural_person) --sanctioned_by-->
(sanction_entry) --listed_on-->
(sanctions_list)

CHAIN B (depth 3 — nominee and beneficial owner):
(company) --directed_by-->
(natural_person) --nominee_for-->
(natural_person) --beneficiary_of-->
(trust) --owned_by-->
(company)

CHAIN C (depth 3 — family + sanctions link):
(natural_person) --family_member_of-->
(natural_person) --holds_position-->
(political_position)
AND the same natural_person --sanctioned_by--> (sanction_entry)

CHAIN D (depth 3 — jurisdiction risk chain):
(company) --owned_by-->
(company) --registered_in-->
(jurisdiction)
with jurisdiction having risk_level = "high"

━━━━━━━━━━━━━━━━━━
SPECIAL INSTRUCTIONS
━━━━━━━━━━━━━━━━━━
- At least one natural_person must have an alias_name V-FACT whose value
  differs from their canonical_name (simulate spelling variation across docs)
- At least one company must be registered in a high-risk jurisdiction
- Ownership percentages should be realistic: controlling stakes ≥ 51%
- Include at least one natural_person who is both a director of one company
  AND a nominee for another person (bridge node)
