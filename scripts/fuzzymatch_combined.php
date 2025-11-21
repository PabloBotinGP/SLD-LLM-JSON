<?php

// Include shared fuzzy matching functions and classes
require_once __DIR__ . '/../src/fuzzymatch.php';

// Test the combined matcher
$matcher = new CombinedMatcher();

// Test data
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

// Run the fuzzy matching
$results = $matcher->fuzzyMatch($searchTerm, $companies, 3, 0.2);

// Display results
FuzzyMatchFunctions::displayCombinedResults($searchTerm, $results);

// Additional test with different search terms
// echo "\n\n" . str_repeat("*", 60) . "\n";
// echo "TESTING WITH DIFFERENT VARIATIONS:\n";
// echo str_repeat("*", 60) . "\n";

// $testTerms = ['eco flow', 'ecoflw', 'eco-flow', 'EcoFlow Inc'];

// foreach ($testTerms as $term) {
//     $results = $matcher->fuzzyMatch($term, $companies, 3, 0.3);
//     echo "\nSearch: '$term' -> Top match: ";
//     if (!empty($results)) {
//         echo "'{$results[0]['match']}' (Score: " . round($results[0]['score'], 3) . ")\n";
//     } else {
//         echo "No matches found\n";
//     }
// }

?>
