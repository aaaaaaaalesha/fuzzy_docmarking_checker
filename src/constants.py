# Copyright 2022 aaaaaaaalesha

DOC_EXTENSIONS = ('.docx', '.xlsx')
IMG_EXTENSIONS = ('.jpg', '.png', '.bmp')
VALID_EXTENSIONS = (*DOC_EXTENSIONS, *IMG_EXTENSIONS)

CORE = 'docProps/core.xml'

DOC_CREATOR_TAG = 'dc:creator'
DOC_DT_CREATED = 'dcterms:created'
DOC_DT_MODIFIED = 'dcterms:modified'
DOC_CORE_PROPERTIES = 'cp:coreProperties'
DOC_CP_KEYWORDS = 'cp:keywords'
DOC_DC_DESCRIPTION = 'dc:description'

# Compare section.
FILE_NAME = 'Filename'

CREATOR_NAME = 'Creator name'
WORKPLACE_NAME = 'Workplace name'
CREATION_TIME = 'Creation time'
MODIFIED_TIME = 'Last modified time'
FUZZY_HASH = 'Fuzzy hash'
IS_HASH_INTEGRITY = 'Hash integrity'

DOC_FIELDS = (
    FILE_NAME,
    CREATOR_NAME,
    WORKPLACE_NAME,
    CREATION_TIME,
    MODIFIED_TIME,
    FUZZY_HASH,
    IS_HASH_INTEGRITY,
)

AVG_HASH = 'Average hash'
DIFF_HASH = 'Difference hash'
PERC_HASH = 'Perceptual hash'
COLOR_HASH = 'HSV color hash'

IMG_FIELDS = (
    AVG_HASH,
    DIFF_HASH,
    PERC_HASH,
    COLOR_HASH,
)

MATCH = '[v]'
MISMATCH = '[ ]'
NOT_FOUND = 'information_not_found'
