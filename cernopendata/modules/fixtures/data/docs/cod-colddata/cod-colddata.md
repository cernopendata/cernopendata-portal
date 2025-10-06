Over the past decade, as the CERN Open Data Portal has grown, so too have the demands on storage: more datasets, more users, and ever more ambitious releases. Today, the portal hosts more than five petabytes of data. And the trend is growing rapidly.  While a substantial fraction is accessed frequently (“hot data”), there is a portion that is rarely used but still must be preserved for reproducibility, future analyses, and educational purposes.

Maintaining all data in high‐performance “hot” storage is expensive and unsustainable. This has led us to explore and now introduce cold storage, a tiered approach that balances cost, durability, and accessibility.

Cold storage refers to storage media and infrastructure optimized for data that is infrequently accessed. Key features include:

<ul>
<li>High durability: Ensuring integrity over long periods.</li>
<li>Cost efficiency: Lower cost per terabyte compared to hot disk or SSD storage.</li>
<li>Long-term preservation: Suitability for archival retention policies.</li>
<li>Acceptable latency: Users may need to “stage” data (retrieve from cold to warm/hot storage) before access; this introduces delays.
</li>
</ul>

We have implemented cold storage using the CERN Tape Archive (<a href="https://cta.docs.cern.ch/v5/">CTA</a>).

A file can therefore be either <strong>online</strong>, if the file is in the hot media, or <strong>offline</strong>, if the file is in cold media.

Since a record can contain multiple files, there are more possible status for a record:
<ul>
<li><strong>Online</strong>: If all the files of the record are online.</li>
<li><strong>Offline</strong>: If all the files of the record are offline.</li>
<li><strong>Partial</strong>: There are some files available online.</li>
<li><strong>Requested</strong>: The record contains at least one file that has been requested for staging and that it is still not online.</li>
</ul>

The records that are not online will include a button to request the staging. Any user can issue such a request. They might also introduce their email, and they will be notified when the staging request has finished. The status of the requests can also be found on a <a href="../transfer_requests">dedicated page</a>.

In conclusion, introducing cold storage is a strategic move to ensure that the CERN Open Data Portal can keep growing — in terms of data volume, longevity, and impact — without compromising cost, preservation, or user expectations.