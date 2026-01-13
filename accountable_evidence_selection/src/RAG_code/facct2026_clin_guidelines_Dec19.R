library(dplyr)

read_metadata= read.csv(file = "../results/clin_guid_metadata_epfl_Oct28.csv", header=TRUE, stringsAsFactors = FALSE)

table(read_metadata$source)
# Removing wikidoc as it is not a clinical guideline

read_metadata1 = subset(read_metadata, source != 'wikidoc')

# 4912 out of 37970 = 12.94%