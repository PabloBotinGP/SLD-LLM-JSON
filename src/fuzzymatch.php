<?php

/**
 * Shared Fuzzy Matching Functions Library
 * 
 * This library provides reusable fuzzy matching functions for fuzzymatching. 
 */

class FuzzyMatchFunctions {
    
    /**
     * Normalize string for comparison
     * 
     * @param string $str - The string to normalize
     * @return string - Normalized string
     */
    public static function normalize($str) {
        // Ensure input is a string
        $str = (string)$str;
        
        // Convert to lowercase
        $str = strtolower($str);
        
        // Remove common company suffixes/prefixes
        $patterns = [
            '/\b(inc|llc|ltd|corp|corporation|company|co|technologies|tech|energy|power|systems?|solutions?)\b\.?/',
            '/\b(the)\s+/',
        ];
        
        foreach ($patterns as $pattern) {
            $str = preg_replace($pattern, '', $str);
        }
        
        // Remove extra whitespace and punctuation
        $str = preg_replace('/[^\w\s]/', '', $str);
        $str = preg_replace('/\s+/', ' ', $str);
        $str = trim($str);
        
        return $str;
    }
    
    /**
     * Jaro Distance implementation
     * 
     * @param string $str1 - First string
     * @param string $str2 - Second string
     * @return float - Jaro distance (0-1)
     */
    public static function jaro($str1, $str2) {
        // Ensure inputs are strings
        $str1 = (string)$str1;
        $str2 = (string)$str2;
        
        $len1 = strlen($str1);
        $len2 = strlen($str2);
        
        if ($len1 === 0 && $len2 === 0) return 1.0;
        if ($len1 === 0 || $len2 === 0) return 0.0;
        
        $matchWindow = (int)(max($len1, $len2) / 2) - 1;
        if ($matchWindow < 0) $matchWindow = 0;
        
        $str1Matches = array_fill(0, $len1, false);
        $str2Matches = array_fill(0, $len2, false);
        
        $matches = 0;
        $transpositions = 0;
        
        // Find matches
        for ($i = 0; $i < $len1; $i++) {
            $start = max(0, (int)($i - $matchWindow));
            $end = min((int)($i + $matchWindow + 1), $len2);
            
            for ($j = $start; $j < $end; $j++) {
                if ($str2Matches[$j] || !isset($str1[$i]) || !isset($str2[$j]) || $str1[$i] !== $str2[$j]) {
                    continue;
                }
                
                $str1Matches[$i] = true;
                $str2Matches[$j] = true;
                $matches++;
                break;
            }
        }
        
        if ($matches === 0) return 0.0;
        
        // Count transpositions
        $k = 0;
        for ($i = 0; $i < $len1; $i++) {
            if (!$str1Matches[$i]) continue;
            
            while ($k < $len2 && !$str2Matches[$k]) $k++;
            
            if ($k < $len2 && isset($str1[$i]) && isset($str2[$k]) && $str1[$i] !== $str2[$k]) {
                $transpositions++;
            }
            $k++;
        }
        
        return ($matches / $len1 + $matches / $len2 + ($matches - $transpositions / 2) / $matches) / 3;
    }
    
    /**
     * Jaro-Winkler Distance implementation
     * Excellent for strings with common prefixes
     * 
     * @param string $str1 - First string
     * @param string $str2 - Second string
     * @return float - Jaro-Winkler distance (0-1)
     */
    public static function jaroWinkler($str1, $str2) {
        // Ensure inputs are strings
        $str1 = (string)$str1;
        $str2 = (string)$str2;
        
        $jaro = self::jaro($str1, $str2);
        
        if ($jaro < 0.7) {
            return $jaro;
        }
        
        // Calculate common prefix length (up to 4 characters)
        $prefix = 0;
        $maxPrefix = min(4, min(strlen($str1), strlen($str2)));
        
        for ($i = 0; $i < $maxPrefix; $i++) {
            if (isset($str1[$i]) && isset($str2[$i]) && $str1[$i] === $str2[$i]) {
                $prefix++;
            } else {
                break;
            }
        }
        
        return $jaro + (0.1 * $prefix * (1 - $jaro));
    }
    
    /**
     * Normalized Levenshtein Distance (returns similarity score 0-1)
     * 
     * @param string $str1 - First string
     * @param string $str2 - Second string
     * @return float - Normalized Levenshtein similarity (0-1)
     */
    public static function normalizedLevenshtein($str1, $str2) {
        // Ensure inputs are strings
        $str1 = (string)$str1;
        $str2 = (string)$str2;
        
        $len1 = strlen($str1);
        $len2 = strlen($str2);
        $maxLen = max($len1, $len2);
        
        if ($maxLen === 0) return 1.0;
        
        $distance = levenshtein($str1, $str2);
        return 1 - ($distance / $maxLen);
    }
    
    /**
     * Token-based similarity for multi-word strings
     * 
     * @param string $str1 - First string
     * @param string $str2 - Second string
     * @return float - Token similarity score (0-1)
     */
    public static function tokenBasedSimilarity($str1, $str2) {
        $tokens1 = array_filter(explode(' ', $str1));
        $tokens2 = array_filter(explode(' ', $str2));
        
        if (empty($tokens1) && empty($tokens2)) return 1.0;
        if (empty($tokens1) || empty($tokens2)) return 0.0;
        
        $intersection = array_intersect($tokens1, $tokens2);
        $union = array_unique(array_merge($tokens1, $tokens2));
        
        // Jaccard similarity
        $jaccard = count($intersection) / count($union);
        
        // Also check for partial token matches
        $partialMatches = 0;
        $totalComparisons = 0;
        
        foreach ($tokens1 as $token1) {
            foreach ($tokens2 as $token2) {
                $totalComparisons++;
                $similarity = self::normalizedLevenshtein($token1, $token2);
                if ($similarity > 0.7) {
                    $partialMatches += $similarity;
                }
            }
        }
        
        $partialScore = $totalComparisons > 0 ? $partialMatches / $totalComparisons : 0;
        
        // Combine Jaccard and partial matching
        return ($jaccard * 0.7) + ($partialScore * 0.3);
    }
    
    /**
     * Soundex-based phonetic similarity
     * 
     * @param string $str1 - First string
     * @param string $str2 - Second string
     * @return float - Soundex similarity score (0-1)
     */
    public static function soundexSimilarity($str1, $str2) {
        // For multi-word strings, compare soundex of each word
        $tokens1 = array_filter(explode(' ', $str1));
        $tokens2 = array_filter(explode(' ', $str2));
        
        if (empty($tokens1) && empty($tokens2)) return 1.0;
        if (empty($tokens1) || empty($tokens2)) return 0.0;
        
        $matches = 0;
        $totalComparisons = 0;
        
        foreach ($tokens1 as $token1) {
            foreach ($tokens2 as $token2) {
                $totalComparisons++;
                if (soundex($token1) === soundex($token2)) {
                    $matches++;
                }
            }
        }
        
        return $totalComparisons > 0 ? $matches / $totalComparisons : 0;
    }
    
    /**
     * Display results for simple Jaro-Winkler matching
     * 
     * @param string $searchTerm - The original search term
     * @param array $results - Array of match results with 'company' and 'score' keys
     */
    public static function displaySimpleResults($searchTerm, $results) {
        echo "\nSearching for: '$searchTerm'\n";
        echo str_repeat("─", 50) . "\n";
        
        if (empty($results)) {
            echo "No matches found\n";
            return;
        }
        
        foreach ($results as $i => $result) {
            $stars = str_repeat("★", (int)($result['score'] * 5));
            echo sprintf("%d. %s (%.3f) %s\n", 
                $i + 1, 
                $result['company'] ?? $result['match'] ?? 'Unknown',
                $result['score'],
                $stars
            );
        }
        echo "\n";
    }
    
    /**
     * Display detailed results for combined matching
     * 
     * @param string $needle - The original search term
     * @param array $results - Array of match results with 'match', 'score', and 'details' keys
     */
    public static function displayCombinedResults($needle, $results) {
        echo "\n" . str_repeat("=", 60) . "\n";
        echo "FUZZY MATCH RESULTS FOR: '$needle'\n";
        echo str_repeat("=", 60) . "\n";
        
        if (empty($results)) {
            echo "No matches found.\n";
            return;
        }
        
        foreach ($results as $i => $result) {
            echo "\n" . ($i + 1) . ". {$result['match']}\n";
            echo "   Overall Score: " . round($result['score'], 3) . "\n";
            echo "   Breakdown:\n";
            foreach ($result['details'] as $algorithm => $score) {
                echo "     - " . ucfirst(str_replace('_', ' ', $algorithm)) . ": $score\n";
            }
        }
        
        echo "\n" . str_repeat("=", 60) . "\n";
    }
}

/**
 * Base Jaro-Winkler Matcher
 * Provides simple Jaro-Winkler matching functionality
 */
class JaroWinklerMatcher {
    
    /**
     * Find best matches using Jaro-Winkler algorithm
     * 
     * @param string $searchTerm - The term to search for
     * @param array $candidates - Array of candidate strings to match against
     * @param int $maxResults - Maximum number of results to return
     * @param float $minScore - Minimum similarity score threshold (0-1)
     * @return array - Sorted array of matches with 'company'/'match' and 'score' keys
     */
    public function findMatches($searchTerm, $candidates, $maxResults = 5, $minScore = 0.6) {
        $results = [];
        
        $searchTerm = FuzzyMatchFunctions::normalize($searchTerm);
        
        foreach ($candidates as $candidate) {
            $normalizedCandidate = FuzzyMatchFunctions::normalize($candidate);
            $score = FuzzyMatchFunctions::jaroWinkler($searchTerm, $normalizedCandidate);
            
            if ($score >= $minScore) {
                $results[] = [
                    'company' => $candidate,
                    'score' => round($score, 3)
                ];
            }
        }
        
        // Sort by score (best first)
        usort($results, fn($a, $b) => $b['score'] <=> $a['score']);
        
        return array_slice($results, 0, $maxResults);
    }
}

/**
 * Combined Matcher
 * Provides composite multi-algorithm matching with weighted scoring
 */
class CombinedMatcher {
    
    private $weights = [
        'jaro_winkler' => 0.4,
        'levenshtein' => 0.3,
        'token_match' => 0.2,
        'soundex' => 0.1
    ];
    
    /**
     * Find best matches using composite scoring
     * 
     * @param string $needle - The search term
     * @param array $haystack - Array of candidate strings to search in
     * @param int $limit - Maximum number of results to return
     * @param float $threshold - Minimum composite score (0-1)
     * @return array - Sorted array of matches with 'match', 'score', and 'details' keys
     */
    public function fuzzyMatch($needle, $haystack, $limit = 5, $threshold = 0.3) {
        $results = [];
        
        // Normalize the search string
        $needle_clean = FuzzyMatchFunctions::normalize($needle);
        
        foreach ($haystack as $candidate) {
            $candidate_clean = FuzzyMatchFunctions::normalize($candidate);
            
            // Calculate combined score
            $score = $this->calculateCombinedScore($needle_clean, $candidate_clean);
            
            if ($score >= $threshold) {
                $results[] = [
                    'match' => $candidate,
                    'score' => $score,
                    'details' => $this->getScoreDetails($needle_clean, $candidate_clean)
                ];
            }
        }
        
        // Sort by score (highest first)
        usort($results, function($a, $b) {
            return $b['score'] <=> $a['score'];
        });
        
        return array_slice($results, 0, $limit);
    }
    
    /**
     * Calculate combined similarity score using multiple algorithms
     */
    private function calculateCombinedScore($str1, $str2) {
        $scores = [
            'jaro_winkler' => FuzzyMatchFunctions::jaroWinkler($str1, $str2),
            'levenshtein' => FuzzyMatchFunctions::normalizedLevenshtein($str1, $str2),
            'token_match' => FuzzyMatchFunctions::tokenBasedSimilarity($str1, $str2),
            'soundex' => FuzzyMatchFunctions::soundexSimilarity($str1, $str2)
        ];
        
        $compositeScore = 0;
        foreach ($scores as $algorithm => $score) {
            $compositeScore += $score * $this->weights[$algorithm];
        }
        
        return $compositeScore;
    }
    
    /**
     * Get detailed breakdown of similarity scores
     */
    private function getScoreDetails($str1, $str2) {
        return [
            'jaro_winkler' => round(FuzzyMatchFunctions::jaroWinkler($str1, $str2), 3),
            'levenshtein' => round(FuzzyMatchFunctions::normalizedLevenshtein($str1, $str2), 3),
            'token_match' => round(FuzzyMatchFunctions::tokenBasedSimilarity($str1, $str2), 3),
            'soundex' => round(FuzzyMatchFunctions::soundexSimilarity($str1, $str2), 3)
        ];
    }
}

?>
