from sklearn.feature_extraction.text import HashingVectorizer


corpus = ["ab", "ac", "aa", "de", "xf", "jjj\xf5jjj", "aaaaaaaaaaaaaaaaaaaaaaaa",
          "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"]

hv = HashingVectorizer(encoding='iso-8859-15')
#print hv.input_type
x = hv.transform(corpus)
print x[0].shape

#print hv