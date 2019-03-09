module SizeInfo (
    sizeInfo
) where

import Text.Printf (printf)

data SizeInfo = SizeInfo {
        fileName :: String,
        width :: Integer,
        height :: Integer
        }
    | EmptySizeInfo

upperSizes = [200, 190, 180, 170, 160, 150, 120, 100, 75, 50]

recordDim :: (Integer -> Integer -> Bool) -> (SizeInfo -> Integer) -> [SizeInfo] -> SizeInfo
recordDim _ _ [] = EmptySizeInfo
recordDim comp getDim xs = foldr getRecord (last xs) (init xs)
    where
        getRecord currSizeInfo acc
            | currDim `comp` accDim = currSizeInfo
            | True = acc
            where
                currDim = getDim currSizeInfo
                accDim = getDim acc

maxDim = recordDim (>)
maxWidth = maxDim width
maxHeight = maxDim height
minDim = recordDim (<)
minWidth = minDim width
minHeight = minDim height

avg :: Real a => [a] -> Double
avg [] = 0
avg xs = fromRational (toRational (sum xs) / toRational (length xs))

avgDim getDim = avg . map getDim

avgWidth = avgDim width
avgHeight = avgDim height

instance Show SizeInfo where
    show (SizeInfo fileName width height) =
            fileName ++ " (" ++ show width ++ "x"
            ++ show height ++ ")"
    show EmptySizeInfo = "Empty SizeInfo"

printDouble :: Double -> String
printDouble = printf "%.2f"

baseStats xs = unlines [
        "Max height: " ++ show (maxHeight xs),
        "Max width: " ++ show (maxWidth xs),
        "Average height: " ++ printDouble (avgWidth xs),
        "Average width: " ++ printDouble (avgWidth xs)
        ]

dropGt :: Integer -> [SizeInfo] -> [SizeInfo]
dropGt size = filter (\x -> height x < size && width x < size)

stats totalInfo = unlines ([
    "Total number of elements: " ++ show totalInfoCount, "",
    "Min height: " ++ show (minHeight totalInfo),
    "Min width: " ++ show (minWidth totalInfo),
    baseStats totalInfo] ++ dropSizesStats totalInfo upperSizes)
    where
        totalInfoCount = length totalInfo
        dropSizesStats [] _ = []
        dropSizesStats _ [] = []
        dropSizesStats info (size:sizes)
            | lessSizeCount == length info = dropSizesStats info sizes
            | True = showInfo : dropSizesStats info sizes
            where
                lessSize = dropGt size info
                lessSizeCount = length lessSize
                droppedCount = totalInfoCount - lessSizeCount
                droppedPerc = (fromIntegral droppedCount) / (fromIntegral totalInfoCount) * 100
                showInfo = unlines [
                        "Dropping elements with height or width greater than "
                        ++ show size ++ "... " ++ printDouble droppedPerc
                        ++ "% elements dropped from total ("
                        ++ show droppedCount ++ ")\n", baseStats lessSize]

(#) :: [a] -> Int -> a
xs # n = (last . take n) xs

sizeInfo = stats . map makeSizeInfo . lines
    where
        makeSizeInfo line
            | null words' = EmptySizeInfo
            | True = SizeInfo (words' # 1) (read (words' # 2)) (read (words' # 3))
            where words' = words line
