"""Demo master data for the two organisations.

Gazipur Zila Parishad keeps the existing directory in services.data.
Everything below is the Dhaka South City Corporation sample set: departments,
zones, wards, services, forms and the three verification stages.
"""

ORGANIZATIONS = [
    dict(
        code='gzp', name='Gazipur Zila Parishad', name_bn='গাজীপুর জেলা পরিষদ',
        title='Gazipur Zila Parishad: Integrated Digital Platform',
        title_bn='গাজীপুর জেলা পরিষদ: সমন্বিত ডিজিটাল সেবা প্ল্যাটফর্ম',
        kind='parishad', head_title='Chairman', head_name='Md. Monowar Hossain',
        address='Zila Parishad Bhaban, Gazipur Sadar, Gazipur',
        phone='+880 1711-000018', theme='parishad', sort=1,
    ),
    dict(
        code='dscc', name='Dhaka South City Corporation', name_bn='ঢাকা দক্ষিণ সিটি কর্পোরেশন',
        title='Dhaka South City Corporation: Integrated Digital Service Platform',
        title_bn='ঢাকা দক্ষিণ সিটি কর্পোরেশন: সমন্বিত ডিজিটাল সেবা প্ল্যাটফর্ম',
        kind='city', head_title='Mayor / Administrator', head_name='Md. Ashikur Rahman',
        address='Nagor Bhaban, 34-37 Fulbaria, Dhaka 1000',
        phone='+880 1711-000075', theme='city', sort=2,
    ),
]

CITY_DEPARTMENTS = [
    {'name': "Office of the Hon'ble Administrator", 'group': 'Executive offices',
     'summary': 'Administrative head of the corporation. Oversees statutory functions, corporation policy and inter-agency coordination.'},
    {'name': 'Office of the Chief Executive Officer', 'group': 'Executive offices',
     'summary': 'Executive head of the corporation. Runs day-to-day administration and supervises every department.'},
    {'name': "Secretary's Office", 'group': 'Executive offices',
     'summary': 'Board and council meeting support, records, official correspondence and gazette publication.'},
    {'name': 'Engineering Department', 'group': 'Engineering and planning',
     'summary': 'Roads, drains, footpaths, bridges and public buildings. Prepares design, estimates and work orders.'},
    {'name': 'ICT Cell', 'group': 'Corporate support',
     'summary': 'Digital services, network, data centre and the online application platform.'},
    {'name': 'Waste Management Department', 'group': 'Civic services',
     'summary': 'Household and commercial waste collection, transfer stations and city cleanliness drives.'},
    {'name': 'Social Welfare and Slum Development Department', 'group': 'Civic services',
     'summary': 'Social safety programmes, slum improvement and support for vulnerable residents.'},
    {'name': 'Stores and Purchase Department', 'group': 'Finance and property',
     'summary': 'Procurement, tenders, stock registers and stores for all corporation offices.'},
    {'name': 'Property Department', 'group': 'Finance and property',
     'summary': 'Corporation land, buildings, markets and leases. Maintains asset records and mutation files.'},
    {'name': 'Public Relations Department', 'group': 'Corporate support',
     'summary': 'Public information, press releases, events and citizen communication.'},
    {'name': 'Revenue Department', 'group': 'Finance and property',
     'summary': 'Holding tax, trade licence fees, rents and other municipal revenue.'},
    {'name': 'Accounting Department', 'group': 'Finance and property',
     'summary': 'Budget, accounts, bill payments and audit coordination.'},
    {'name': 'Department of Transportation', 'group': 'Engineering and planning',
     'summary': 'Traffic management coordination, transport terminals and vehicle licensing support.'},
    {'name': 'Health Department', 'group': 'Civic services',
     'summary': 'Public health, sanitation, vaccination drives, food safety and health centres.'},
    {'name': 'Urban Planning Department', 'group': 'Engineering and planning',
     'summary': 'Master plan, land use, building plan approval and development control.'},
    {'name': 'Law Department', 'group': 'Corporate support',
     'summary': 'Legal opinions, court cases, contracts and enforcement of corporation laws.'},
]

CITY_OFFICE_GROUPS = ['Executive offices', 'Engineering and planning', 'Civic services',
                      'Finance and property', 'Corporate support']

CITY_LEGAL_DOCUMENTS = [
    {'category': 'gazette', 'year': '2024', 'title': 'Dhaka South City Corporation Gazette Notification',
     'reference': 'DSCC/Gazette/2024/07',
     'summary': 'Publication of ward boundaries, office jurisdictions and service counters notified by the corporation.'},
    {'category': 'gazette', 'year': '2022', 'title': 'Local Government (City Corporation) Gazette Amendment',
     'reference': 'LGD/Gazette/2022/19',
     'summary': 'Amendment to the city corporation rules covering service delivery, ward committees and public notices.'},
    {'category': 'gazette', 'year': '2016', 'title': 'Dhaka South City Corporation Formation Gazette',
     'reference': 'LGD/Gazette/2016/02',
     'summary': 'Notification constituting Dhaka South City Corporation and defining its territorial limits.'},
    {'category': 'law', 'year': '2009', 'title': 'Local Government (City Corporation) Act, 2009',
     'reference': 'Act No. 60 of 2009',
     'summary': 'Principal law for city corporation administration, taxation, licensing and municipal services.'},
    {'category': 'law', 'year': '2016', 'title': 'Local Government (City Corporation) Amendment Act, 2016',
     'reference': 'Act No. 15 of 2016',
     'summary': 'Updates to service obligations, ward-level governance and the corporation budget process.'},
    {'category': 'law', 'year': '2019', 'title': 'City Corporation Service Rules Act, 2019',
     'reference': 'Act No. 32 of 2019',
     'summary': 'Citizen service standards, application handling timelines and departmental accountability.'},
    {'category': 'rules', 'year': '2023', 'title': 'Dhaka South City Corporation Building Construction Rules, 2023',
     'reference': 'DSCC/Rules/2023/04',
     'summary': 'Building plan submission, approval stages and inspection requirements for construction within corporation limits.'},
    {'category': 'rules', 'year': '2021', 'title': 'City Corporation Trade Licence Rules, 2021',
     'reference': 'DSCC/Rules/2021/11',
     'summary': 'Trade licence categories, renewal timelines, fees and the documents required with each application.'},
    {'category': 'rules', 'year': '2020', 'title': 'Waste Management and Sanitation Rules, 2020',
     'reference': 'DSCC/Rules/2020/09',
     'summary': 'Waste collection schedules, segregation duties, penalties and the complaint process for citizens.'},
]

CITY_LEGAL_CATEGORIES = [
    ('gazette', 'Gazette'),
    ('law', 'Act'),
    ('rules', 'Rules'),
]

ZONES = [
    (1, 'Kotwali', 'কোতোয়ালী', 8),
    (2, 'Sutrapur', 'সূত্রাপুর', 8),
    (3, 'Motijheel', 'মতিঝিল', 8),
    (4, 'Sabujbagh', 'সবুজবাগ', 8),
    (5, 'Khilgaon', 'খিলগাঁও', 8),
    (6, 'Jatrabari', 'যাত্রাবাড়ী', 8),
    (7, 'Demra', 'ডেমরা', 8),
    (8, 'Shyampur', 'শ্যামপুর', 7),
    (9, 'Lalbagh', 'লালবাগ', 7),
    (10, 'South Keraniganj', 'দক্ষিণ কেরানীগঞ্জ', 5),
]

COUNCILLOR_FIRST = [
    'Md. Shahidul', 'Md. Kamrul', 'Md. Rafiqul', 'Syeda', 'Md. Anwar',
    'Mst. Nasima', 'Md. Habibur', 'Md. Nazrul', 'Mst. Rokeya', 'Md. Jasim',
    'Md. Faruk', 'Mst. Shirin',
]
COUNCILLOR_LAST = [
    'Islam', 'Hossain', 'Rahman', 'Akter', 'Ahmed', 'Begum', 'Chowdhury',
]


def councillor_name(number):
    first = COUNCILLOR_FIRST[(number - 1) % len(COUNCILLOR_FIRST)]
    last = COUNCILLOR_LAST[(number - 1) % len(COUNCILLOR_LAST)]
    return f'{first} {last}'


CITY_SERVICES = [
    dict(code='trade-licence', name='Trade Licence', name_bn='ট্রেড লাইসেন্স',
         icon='shop', department='Revenue Department', fee=1500, processing_days=7,
         summary='New trade licence, renewal, amendment and food business licence for '
                 'shops and businesses inside the corporation area.',
         requirements='National ID of the owner\nTrade name and business address\nRent '
                      'agreement or ownership document\nTax identification number, if any'),
    dict(code='birth-registration', name='Birth Registration', name_bn='জন্ম নিবন্ধন',
         icon='person-vcard', department='Health Department', fee=0, processing_days=3,
         summary='Register a birth and collect the birth registration certificate.',
         requirements='Hospital or midwife certificate\nNational ID of both parents\nWard '
                      'number\nMobile number'),
    dict(code='death-registration', name='Death Registration', name_bn='মৃত্যু নিবন্ধন',
         icon='file-earmark-medical', department='Health Department', fee=0, processing_days=3,
         summary='Register a death and collect the death registration certificate.',
         requirements='Death certificate or hospital certificate\nNational ID of the '
                      'deceased, if available\nNational ID of the informant'),
    dict(code='holding-tax', name='Holding Tax', name_bn='হোল্ডিং ট্যাক্স',
         icon='receipt', department='Revenue Department', fee=0, processing_days=5,
         summary='Holding tax assessment, name mutation and tax clearance for a holding.',
         requirements='Holding number and ward\nMutation deed or inheritance certificate\n'
                      'National ID of the owner\nPrevious tax receipt'),
    dict(code='building-plan', name='Building Plan', name_bn='বিল্ডিং প্ল্যান',
         icon='buildings', department='Urban Planning Department', fee=5000, processing_days=30,
         summary='Approval of a new building plan, revision and completion certificate.',
         requirements='Land ownership document and khatian\nArchitectural and structural '
                      'drawings\nSoil test report\nWard councillor recommendation'),
    dict(code='signboard', name='Signboard & Ads', name_bn='সাইনবোর্ড ও বিজ্ঞাপন',
         icon='badge-ad', department='Revenue Department', fee=2000, processing_days=7,
         summary='Permission for a signboard or advertisement and the annual advertisement '
                 'tax return.',
         requirements='Photograph or design of the signboard\nSize and location\nBusiness '
                      'trade licence\nNational ID'),
    dict(code='market-stall', name='Market Stall', name_bn='মার্কেট স্টল',
         icon='shop-window', department='Property Department', fee=1000, processing_days=10,
         summary='Apply for a shop or stall in a corporation market and pay the allotment fee.',
         requirements='National ID\nTrade licence, if already issued\nCategory of goods\n'
                      'Ward number'),
    dict(code='road-cutting', name='Road Cutting', name_bn='রাস্তা কাটা',
         icon='cone-striped', department='Engineering Department', fee=3000, processing_days=10,
         summary='Permission to cut a corporation road, footpath or drain for utility work.',
         requirements='Work description and drawing\nUtility authority letter\nRestoration '
                      'plan and timeline\nNational ID of the contractor'),
    dict(code='event-permission', name='Event Permission', name_bn='ইভেন্টের অনুমতি',
         icon='calendar-event', department='Public Relations Department', fee=2500,
         processing_days=5,
         summary='Permission for a public event, rally, fair or stage programme in the '
                 'corporation area.',
         requirements='Event description and purpose\nDate, time and venue\nOrganiser '
                      'National ID\nSecurity and traffic plan'),
    dict(code='conservancy', name='Waste Collection Fee', name_bn='বর্জ্য সংগ্রহ ফি',
         icon='trash', department='Waste Management Department', fee=500, processing_days=3,
         summary='Conservancy service, waste collection arrangement and exemption requests.',
         requirements='Holding number and ward\nBusiness type\nNumber of collection points\n'
                      'National ID'),
    dict(code='citizen-certificate', name='Citizen Certificate', name_bn='নাগরিক সনদ',
         icon='patch-check', department='Revenue Department', fee=100, processing_days=2,
         summary='Residence, citizenship and ward councillor recommendation certificates.',
         requirements='National ID\nWard number\nPurpose of the certificate\nPassport-size '
                      'photograph'),
    dict(code='complaint', name='Complaint', name_bn='অভিযোগ',
         icon='megaphone', department="Office of the Hon'ble Administrator", fee=0,
         processing_days=5,
         summary='Report a civic problem, submit a grievance and track the corporation reply.',
         requirements='Description of the problem\nLocation and ward number\nPhotograph, if '
                      'available\nMobile number'),
    dict(code='marriage-registration', name='Marriage Registration', name_bn='বিবাহ নিবন্ধন',
         icon='heart', department='Health Department', fee=0, processing_days=3,
         summary='Register a marriage and collect the marriage certificate.',
         requirements='National ID of both parties\nTwo witness National IDs\nWard number\n'
                      'Marriage date|date'),
    dict(code='financial-assistance', name='Financial Help',
         name_bn='আর্থিক সহায়তা', icon='cash-coin',
         department='Social Welfare and Slum Development Department', fee=0, processing_days=15,
         summary='Financial assistance for people affected by a natural disaster, disability, '
                 'incurable disease or an accident, and for the family of a deceased employee.',
         requirements='National ID or birth certificate (attested copy)\nTwo attested passport '
                      'size photographs\nProof of the nature of the application (attested copy)'),
]

CITY_FORMS = [
    (1, 'Trade licence application (new)', 'ট্রেড লাইসেন্স আবেদন (নতুন)', 'trade-licence',
     'licence', 'city', True,
     ['Applicant name', "Father's / husband's name", 'National ID number|nid', 'Mobile number|mobile',
      'Trade name', 'Business address', 'Ward number', 'Nature of business',
      'Business capital', 'Number of employees', 'Attachments|attach']),
    (2, 'Trade licence renewal application', 'ট্রেড লাইসেন্স নবায়ন আবেদন', 'trade-licence',
     'renewal', 'city', False,
     ['Licence holder name', 'Trade licence number', 'Trade name', 'Business address',
      'Ward number', 'Renewal year', 'Previous tax receipt number', 'Mobile number|mobile']),
    (3, 'Birth registration application', 'জন্ম নিবন্ধন আবেদন', 'birth-registration',
     'application', 'city', True,
     ['Child name', "Father's name", "Mother's name", 'Date of birth|date', 'Place of birth',
      'Gender|select|Male;Female;Other', 'Ward number', 'Informant name', 'Mobile number|mobile']),
    (4, 'Death registration application', 'মৃত্যু নিবন্ধন আবেদন', 'death-registration',
     'application', 'city', False,
     ['Deceased name', "Father's / husband's name", 'Date of death|date', 'Place of death',
      'National ID number|nid', 'Informant name', 'Ward number', 'Mobile number|mobile']),
    (5, 'Holding tax assessment application', 'হোল্ডিং ট্যাক্স নির্ধারণ আবেদন', 'holding-tax',
     'application', 'city', False,
     ['Owner name', 'Holding number', 'Ward number', 'Plot number', 'Khatian number',
      'Land area', 'Building area in square feet', 'Premises type', 'Mobile number|mobile']),
    (6, 'Holding tax name mutation application', 'হোল্ডিং ট্যাক্স নামজারি আবেদন', 'holding-tax',
     'application', 'city', False,
     ['Applicant name', 'Previous owner name', 'Holding number', 'Ward number',
      'Mutation deed number', 'Inheritance certificate number', 'Mobile number|mobile',
      'Attachments|attach']),
    (7, 'Building plan approval application', 'বিল্ডিং প্ল্যান অনুমোদন আবেদন', 'building-plan',
     'application', 'city', True,
     ['Applicant name', 'Owner name', 'Plot number', 'Khatian number', 'Ward number',
      'Plan type', 'Land area', 'Proposed floor area', 'Number of floors',
      'Architect name and licence', 'Attachments|attach']),
    (8, 'Building completion certificate application',
     'ভবন নির্মাণ সমাপ্তি সনদ আবেদন', 'building-plan', 'information', 'city', False,
     ['Applicant name', 'Approved plan number', 'Plot number', 'Ward number',
      'Completion date', 'Engineer name', 'Gross floor area', 'Mobile number|mobile']),
    (9, 'Signboard permission application', 'সাইনবোর্ড স্থাপনের অনুমতি আবেদন', 'signboard',
     'licence', 'city', False,
     ['Applicant name', 'Trade name', 'Business address', 'Ward number', 'Signboard size',
      'Signboard text', 'Location', 'Mobile number|mobile', 'Attachments|attach']),
    (10, 'Advertisement tax return', 'বিজ্ঞাপন করের রিটার্ন', 'signboard', 'information',
     'city', False,
     ['Trade name', 'Trade licence number', 'Ward number', 'Assessment year',
      'Number of signboards', 'Total advertisement area', 'Tax amount', 'Mobile number|mobile']),
    (11, 'Market stall allotment application', 'মার্কেট স্টল বরাদ্দ আবেদন', 'market-stall',
     'application', 'city', False,
     ['Applicant name', 'National ID number|nid', 'Market name', 'Stall category', 'Ward number',
      'Category of goods', 'Deposit amount', 'Mobile number|mobile']),
    (12, 'Road cutting permission application', 'রাস্তা কাটার অনুমতি আবেদন', 'road-cutting',
     'licence', 'city', False,
     ['Contractor name', 'Utility authority', 'Road name', 'Ward number', 'Length in feet',
      'Width in feet', 'Work duration', 'Restoration plan', 'Mobile number|mobile']),
    (13, 'Public event permission application', 'পাবলিক ইভেন্টের অনুমতি আবেদন',
     'event-permission', 'licence', 'city', False,
     ['Organiser name', 'Event description', 'Venue', 'Ward number', 'Event date',
      'Start time', 'Number of participants', 'Security plan', 'Mobile number|mobile']),
    (14, 'Conservancy fee exemption application', 'পরিচ্ছন্নতা ফি মওকুফ আবেদন', 'conservancy',
     'application', 'city', False,
     ['Applicant name', 'Holding number', 'Ward number', 'Business type',
      'Monthly fee amount', 'Reason for exemption', 'Mobile number|mobile']),
    (15, 'Citizen certificate application', 'নাগরিক সনদ আবেদন', 'citizen-certificate',
     'information', 'city', False,
     ['Applicant name', "Father's / husband's name", 'National ID number|nid', 'Ward number',
      'Full address', 'Purpose of the certificate', 'Mobile number|mobile', 'Attachments|attach']),
    (16, 'Marriage registration application', 'বিবাহ নিবন্ধন আবেদন', 'marriage-registration',
     'application', 'city', False,
     ['Bridegroom name', "Bridegroom's father name", 'Bride name', "Bride's father name",
      'National ID of bridegroom', 'National ID of bride', 'Marriage date|date', 'Ward number',
      'Witness one', 'Witness two']),
    (17, 'Complaint and grievance form', 'অভিযোগ ও নালিশ ফরম', 'complaint', 'information',
     'city', False,
     ['Applicant name', 'Mobile number|mobile', 'Ward number', 'Location', 'Complaint category|select|Roads and drains;Waste;Waterlogging;Street lights;Health;Other',
      'Description of the problem', 'Attachments|attach']),
    (18, 'Ward councillor recommendation application',
     'ওয়ার্ড কাউন্সিলরের সুপারিশ আবেদন', 'citizen-certificate', 'application', 'city', False,
     ['Applicant name', 'National ID number|nid', 'Ward number', 'Purpose|text',
      'Full address', 'Mobile number|mobile']),
    (19, 'Food business licence application', 'খাদ্য ব্যবসার লাইসেন্স আবেদন', 'trade-licence',
     'licence', 'city', False,
     ['Applicant name', 'Business name', 'Business address', 'Ward number',
      'Food category', 'Number of food handlers', 'Health clearance number', 'Mobile number|mobile']),
    (20, 'Trade licence amendment application', 'ট্রেড লাইসেন্স সংশোধন আবেদন', 'trade-licence',
     'application', 'city', False,
     ['Applicant name', 'Trade licence number', 'Trade name', 'Ward number',
      'Field to amend', 'Old value', 'New value', 'Reason', 'Mobile number|mobile']),
    (21, 'Application for financial assistance', 'আর্থিক সহায়তার জন্য আবেদন',
     'financial-assistance', 'application', 'city', True,
     ['# Applicant',
      "Applicant's name in Bangla",
      "Applicant's name in English (capital letters)",
      'National ID number|nid',
      'Birth registration number (optional)',
      'Gender|radio|Female;Male;Hijra',
      'Religion|radio|Islam;Hindu;Buddhist;Christian;Other',
      'Nature of application|select|Natural disaster;Physical or mental disability;'
      'Incurable disease;Accident or permanent disability;'
      'Employee or family of a deceased employee;Other',
      'Other subject detail (optional)|textarea',
      'Profession',
      'Mobile number|mobile',
      'Previous financial assistance date (optional)|date',
      '# Permanent address',
      'House / holding no',
      'Road name and no',
      'Block / sector / mouza / mahalla / area',
      'Village',
      'Post office',
      'Postcode|number',
      'Union / ward',
      'Upazila',
      'Thana',
      'City corporation / municipality',
      'District',
      '# Guardian and attachments',
      'Guardian name (optional, if the applicant is a minor)',
      'Guardian contact (optional)|mobile',
      'Attachments|attach']),
]

VERIFICATION_STAGES = [
    (1, 'dscc_councillor', 'Ward councillor verification', False),
    (2, 'dscc_officer', 'Department verification', False),
    (3, 'dscc_mayor', 'Final approval', True),
]

CITY_ACCOUNTS = [
    ('dscc_mayor', 'Md. Ashikur Rahman', 'dscc_mayor', 'Mayor / Administrator', 'dscc'),
    ('dscc_councillor', 'Md. Shahidul Islam', 'dscc_councillor', 'Ward Councillor', 'dscc'),
    ('dscc_officer', 'Farhana Akter', 'dscc_officer', 'Department Officer', 'dscc'),
    ('dscc_citizen', 'Rakib Hasan', 'citizen', 'Citizen / Applicant', 'dscc'),
]
