<?php

// Include shared fuzzy matching functions and classes
require_once __DIR__ . '/../src/fuzzymatch.php';

// Test the Jaro-Winkler matcher
$matcher = new JaroWinklerMatcher();

$searchTerm = 'Ecoflow';

$companies = [
    'ABB',
    'AIMS Power Inc.',
    'Afore New Energy Technology (Shanghai) Co., Ltd.',
    'Alpha ESS Co., Ltd.',
    'Altenergy Power System Inc.',
    'Amensolar Ess Co., Ltd',
    'Anker Innovations Limited',
    'Aptos Solar Technology LLC',
    'CSI Solar Co., Ltd.',
    'Cherry Solution Co., Ltd.',
    'Chilicon Power, LLC',
    'Chint Power Systems America',
    'Darfon Electronics Corp.',
    'Delta Electronics',
    'Dyness Digital Energy Technology Co., LTD.',
    'EG4 Electronics LLC',
    'EPC Power Corp.',
    'EcoFlow Inc.',
    'Energizer Solar',
    'Enphase Energy, Inc.',
    'FOXESS CO., LTD.',
    'Fortress Power LLC',
    'FranklinWH Energy Storage Inc.',
    'Fronius International GmbH',
    'Generac Power Systems, Inc.',
    'General Motors Energy LLC',
    'Geneverse Energy Inc.',
    'Ginlong Technologies Co., Ltd.',
    'GoodWe Technologies Co., Ltd.'
];

// Find and display matches
$results = $matcher->findMatches($searchTerm, $companies);
FuzzyMatchFunctions::displaySimpleResults($searchTerm, $results);

// Test a few more variations
$testTerms = ['eco flow', 'EcoFlow Inc', 'ecoflw', 'Anker'];

foreach ($testTerms as $term) {
    $results = $matcher->findMatches($term, $companies, 3);
    FuzzyMatchFunctions::displaySimpleResults($term, $results);
}

?>